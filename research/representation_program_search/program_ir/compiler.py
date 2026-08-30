"""Deterministic constructor for exact verifier obligations.

The constructor performs typed symbolic execution only.  It deliberately does
not call ``simplify()``, ``equals()``, or the verifier, and it never emits a
proof verdict.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any, Mapping

import sympy

from symbolic_compactification import load_expression
from symbolic_compactification.models import AdapterError, normalize_symbols
from symbolic_compactification.parser import parse_expression, syms_like

from research.representation_program_search.grammar_v1 import (
    G_PRIMITIVE_OPS,
    GRAMMAR_ID,
    LATENT_FORMS,
    OPERATORS,
)

from .canonical import canonical_program_hash
from .model import (
    CompileContext,
    CompiledObligation,
    CompilationResult,
    LatentObject,
    Operator,
    RepresentationProgram,
    thaw_json,
)

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_ALLOWED_ARGUMENTS: dict[str, frozenset[str]] = {
    "VALUE": frozenset({"node", "values"}),
    "SUBSTITUTE": frozenset({"parameter", "value"}),
    "DERIVATIVE": frozenset({"variable", "order"}),
    "SHIFT": frozenset({"variable", "delta"}),
    "PERMUTE": frozenset({"mapping"}),
    "NEWTON_DD": frozenset({"nodes"}),
    "HERMITE_DD": frozenset({"nodes"}),
    "RECURRENCE": frozenset({"parameter", "base", "step", "form"}),
    "LINEAR_COMBINATION": frozenset({"coefficients", "constant"}),
    "BASIS_PROJECT": frozenset({"basis", "coefficient"}),
    "BASIS_RECONSTRUCT": frozenset({"coefficients", "constant"}),
    "COMPOSE": frozenset(),
}


class _CompileFailure(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _fail(code: str, identifier: str | None = None) -> None:
    if identifier is not None:
        raise _CompileFailure(f"{code}:{identifier}")
    raise _CompileFailure(code)


def _ids_unique(items: tuple[Any, ...], attribute: str, code: str) -> None:
    values = [getattr(item, attribute) for item in items]
    if len(values) != len(set(values)):
        _fail(code)


def _safe_member_path(root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if (
        relative_path.is_absolute()
        or len(relative_path.parts) != 2
        or relative_path.parts[0] != "members"
    ):
        _fail("SOURCE_PATH_NOT_MEMBER_ARTIFACT", relative)
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        _fail("SOURCE_PATH_ESCAPE", relative)
    if candidate.suffix != ".txt":
        _fail("SOURCE_PATH_NOT_EXPRESSION", relative)
    return candidate


class _Constructor:
    def __init__(self, program: RepresentationProgram, context: CompileContext):
        self.program = program
        self.context = context
        try:
            self.declared_symbols = normalize_symbols(list(context.symbols))
        except AdapterError as exc:
            _fail(exc.code)
        self.declared_names = {item["name"] for item in self.declared_symbols}
        self.latents: dict[str, tuple[LatentObject, sympy.Expr, dict[str, sympy.Symbol]]] = {}
        self.nodes = {item.node_id: item for item in program.node_structures}
        self.outputs: dict[str, sympy.Expr] = {}
        self.operator_by_output: dict[str, Operator] = {}
        self.source_records: dict[str, Any] = {}

    def validate_common(self) -> None:
        if self.program.grammar_version != GRAMMAR_ID:
            _fail("GRAMMAR_VERSION_UNKNOWN", self.program.grammar_version)
        if self.context.grammar_id not in {"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"}:
            _fail("GRAMMAR_ABLATION_UNKNOWN", self.context.grammar_id)
        _ids_unique(self.program.source_members, "member_id", "SOURCE_MEMBER_DUPLICATE")
        _ids_unique(self.program.latent_objects, "latent_id", "LATENT_ID_DUPLICATE")
        _ids_unique(self.program.node_structures, "node_id", "NODE_ID_DUPLICATE")
        _ids_unique(self.program.operators, "operator_id", "OPERATOR_ID_DUPLICATE")
        _ids_unique(self.program.member_assignments, "member_id", "MEMBER_ASSIGNMENT_DUPLICATE")
        _ids_unique(self.program.obligations, "obligation_id", "OBLIGATION_ID_DUPLICATE")
        if not self.program.source_members:
            _fail("SOURCE_MEMBERS_MISSING")

        for assumption in self.program.assumptions_used:
            status = self.program.assumption_statuses.get(assumption)
            if status not in {"DECLARED", "DERIVED"}:
                _fail("ASSUMPTION_NOT_DECLARED", assumption)

        self._load_sources()
        self._load_latents()

        allowed = set(OPERATORS)
        if self.context.grammar_id == "G_NO_HERMITE":
            allowed.remove("HERMITE_DD")
        elif self.context.grammar_id == "G_PRIMITIVE":
            allowed = set(G_PRIMITIVE_OPS)
        operator_ids = {item.operator_id for item in self.program.operators}
        outputs: set[str] = set()
        for operator in self.program.operators:
            if operator.operator not in OPERATORS:
                _fail("OPERATOR_UNKNOWN", operator.operator)
            if operator.operator not in allowed:
                _fail("OPERATOR_FORBIDDEN_BY_ABLATION", operator.operator_id)
            if operator.latent_id is None:
                _fail("OPERATOR_LATENT_MISSING", operator.operator_id)
            if operator.latent_id not in self.latents:
                _fail("OPERATOR_LATENT_UNKNOWN", operator.latent_id)
            if operator.output is None:
                _fail("OPERATOR_OUTPUT_MISSING", operator.operator_id)
            if operator.output in outputs:
                _fail("OPERATOR_OUTPUT_DUPLICATE", operator.output)
            if operator.output in operator_ids:
                _fail("OUTPUT_ALIASES_OPERATOR_ID", operator.output)
            outputs.add(operator.output)
            unknown_args = set(operator.arguments) - _ALLOWED_ARGUMENTS[operator.operator]
            if unknown_args:
                _fail("OPERATOR_ARGUMENT_UNKNOWN", operator.operator_id)

        source_ids = set(self.source_records)
        assigned_ids = {item.member_id for item in self.program.member_assignments}
        unexplained_ids = set(self.program.unexplained_members)
        overlap = assigned_ids & unexplained_ids
        if overlap:
            _fail("MEMBER_BOTH_ASSIGNED_AND_UNEXPLAINED", sorted(overlap)[0])
        if assigned_ids | unexplained_ids != source_ids:
            _fail("SOURCE_MEMBER_ACCOUNTING_INCOMPLETE")
        for member in self.program.member_assignments:
            if member.member_id not in source_ids:
                _fail("SOURCE_MEMBER_UNKNOWN", member.member_id)
            if member.output is None:
                _fail("MEMBER_ASSIGNMENT_OUTPUT_MISSING", member.member_id)
            for operator_id in member.operator_ids:
                if operator_id not in operator_ids:
                    _fail("MEMBER_OPERATOR_UNKNOWN", operator_id)
        for member_id in self.program.unexplained_members:
            if member_id not in source_ids:
                _fail("UNEXPLAINED_MEMBER_UNKNOWN", member_id)

    def _load_sources(self) -> None:
        for source in self.program.source_members:
            if not re.fullmatch(r"[0-9a-f]{64}", source.sha256):
                _fail("SOURCE_HASH_INVALID", source.member_id)
            path = _safe_member_path(self.context.package_root, source.path)
            try:
                raw = path.read_bytes()
            except OSError:
                _fail("SOURCE_MEMBER_MISSING", source.member_id)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != source.sha256:
                _fail("SOURCE_HASH_MISMATCH", source.member_id)
            try:
                record = load_expression(
                    path,
                    self.declared_symbols,
                    functions=list(self.context.functions) or None,
                )
            except AdapterError as exc:
                _fail(f"SOURCE_PARSE_{exc.code}", source.member_id)
            self.source_records[source.member_id] = record

    def _load_latents(self) -> None:
        for latent in self.program.latent_objects:
            if latent.form not in LATENT_FORMS:
                _fail("LATENT_FORM_UNKNOWN", latent.latent_id)
            if not latent.parameters or any(
                not _IDENTIFIER.fullmatch(item) for item in latent.parameters
            ):
                _fail("LATENT_PARAMETERS_INVALID", latent.latent_id)
            if len(set(latent.parameters)) != len(latent.parameters):
                _fail("LATENT_PARAMETER_DUPLICATE", latent.latent_id)
            collision = set(latent.parameters) & self.declared_names
            if collision:
                _fail("BOUND_PARAMETER_COLLISION", sorted(collision)[0])
            augmented = list(self.declared_symbols) + [
                {"name": parameter, "real": False, "nonzero": False}
                for parameter in latent.parameters
            ]
            try:
                expression = parse_expression(
                    latent.expression,
                    augmented,
                    functions=list(self.context.functions) or None,
                )
            except AdapterError as exc:
                _fail(f"LATENT_PARSE_{exc.code}", latent.latent_id)
            parameters = {
                name: symbol
                for name, symbol in zip(
                    latent.parameters, syms_like(expression, list(latent.parameters))
                )
            }
            self.latents[latent.latent_id] = (latent, expression, parameters)

    def _parse(self, value: Any, code: str) -> sympy.Expr:
        if not isinstance(value, str) or not value.strip():
            _fail(code)
        try:
            return parse_expression(
                value,
                self.declared_symbols,
                functions=list(self.context.functions) or None,
            )
        except AdapterError as exc:
            _fail(f"{code}_{exc.code}")

    def _latent(self, operator: Operator) -> tuple[LatentObject, sympy.Expr, dict[str, sympy.Symbol]]:
        if operator.latent_id is None:
            _fail("OPERATOR_LATENT_MISSING", operator.operator_id)
        if operator.latent_id not in self.latents:
            _fail("OPERATOR_LATENT_UNKNOWN", operator.latent_id)
        return self.latents[operator.latent_id]

    def _inputs(self, operator: Operator) -> list[sympy.Expr]:
        result: list[sympy.Expr] = []
        for reference in operator.inputs:
            if reference not in self.outputs:
                _fail("OPERATOR_INPUT_UNAVAILABLE", reference)
            result.append(self.outputs[reference])
        return result

    def _argument_map(self, operator: Operator, key: str) -> Mapping[str, Any]:
        value = operator.arguments.get(key)
        if not isinstance(value, Mapping):
            _fail("OPERATOR_ARGUMENT_INVALID", operator.operator_id)
        return value

    def _parameter(self, operator: Operator, name: Any, parameters: Mapping[str, sympy.Symbol]) -> sympy.Symbol:
        if not isinstance(name, str) or name not in parameters:
            _fail("LATENT_PARAMETER_UNKNOWN", operator.operator_id)
        return parameters[name]

    def execute(self) -> None:
        for operator in self.program.operators:
            expression = self._execute_one(operator)
            assert operator.output is not None
            self.outputs[operator.output] = expression
            self.operator_by_output[operator.output] = operator

    def _execute_one(self, operator: Operator) -> sympy.Expr:
        kind = operator.operator
        inputs = self._inputs(operator)
        args = thaw_json(operator.arguments)
        if kind == "VALUE":
            if inputs:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            latent, expression, parameters = self._latent(operator)
            if "node" in args:
                if len(latent.parameters) != 1 or "values" in args:
                    _fail("VALUE_ARGUMENT_INVALID", operator.operator_id)
                replacements = {
                    parameters[latent.parameters[0]]: self._parse(args["node"], "VALUE_NODE_INVALID")
                }
            else:
                values = self._argument_map(operator, "values")
                if set(values) != set(latent.parameters):
                    _fail("VALUE_ARGUMENT_INVALID", operator.operator_id)
                replacements = {
                    parameters[name]: self._parse(values[name], "VALUE_NODE_INVALID")
                    for name in latent.parameters
                }
            return expression.xreplace(replacements)

        if kind == "SUBSTITUTE":
            if len(inputs) > 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            _latent, latent_expression, parameters = self._latent(operator)
            parameter = self._parameter(operator, args.get("parameter"), parameters)
            value = self._parse(args.get("value"), "SUBSTITUTE_VALUE_INVALID")
            return (inputs[0] if inputs else latent_expression).xreplace({parameter: value})

        if kind == "DERIVATIVE":
            if len(inputs) > 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            _latent, latent_expression, parameters = self._latent(operator)
            variable_name = args.get("variable")
            if variable_name in parameters:
                variable = parameters[variable_name]
            else:
                variable = self._parse(variable_name, "DERIVATIVE_VARIABLE_INVALID")
                if not isinstance(variable, sympy.Symbol):
                    _fail("DERIVATIVE_VARIABLE_INVALID", operator.operator_id)
            order = args.get("order", 1)
            if not isinstance(order, int) or isinstance(order, bool) or order < 1 or order > 16:
                _fail("DERIVATIVE_ORDER_INVALID", operator.operator_id)
            return sympy.diff(inputs[0] if inputs else latent_expression, variable, order)

        if kind == "SHIFT":
            if len(inputs) > 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            _latent, latent_expression, parameters = self._latent(operator)
            variable_name = args.get("variable")
            if variable_name in parameters:
                variable = parameters[variable_name]
            else:
                variable = self._parse(variable_name, "SHIFT_VARIABLE_INVALID")
                if not isinstance(variable, sympy.Symbol):
                    _fail("SHIFT_VARIABLE_INVALID", operator.operator_id)
            delta = self._parse(args.get("delta"), "SHIFT_DELTA_INVALID")
            return (inputs[0] if inputs else latent_expression).xreplace(
                {variable: variable + delta}
            )

        if kind == "PERMUTE":
            if len(inputs) != 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            mapping = self._argument_map(operator, "mapping")
            replacements: dict[sympy.Expr, sympy.Expr] = {}
            for source, target in mapping.items():
                source_expression = self._parse(source, "PERMUTE_SOURCE_INVALID")
                if not isinstance(source_expression, sympy.Symbol):
                    _fail("PERMUTE_SOURCE_INVALID", operator.operator_id)
                replacements[source_expression] = self._parse(target, "PERMUTE_TARGET_INVALID")
            return inputs[0].xreplace(replacements)

        if kind in {"NEWTON_DD", "HERMITE_DD"}:
            if inputs:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            latent, expression, parameters = self._latent(operator)
            if latent.form not in {"FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION"} or len(latent.parameters) != 1:
                _fail("DIVIDED_DIFFERENCE_LATENT_INVALID", operator.operator_id)
            node_id = args.get("nodes")
            if not isinstance(node_id, str) or node_id not in self.nodes:
                _fail("NODE_STRUCTURE_UNKNOWN", operator.operator_id)
            labels = self.nodes[node_id].nodes
            if len(labels) < 2:
                _fail("NODE_ARITY_INVALID", node_id)
            if kind == "NEWTON_DD" and len(set(labels)) != len(labels):
                _fail("NEWTON_REPEATED_NODE", node_id)
            if kind == "HERMITE_DD":
                if len(set(labels)) == len(labels):
                    _fail("HERMITE_REPEATED_NODE_REQUIRED", node_id)
                seen: set[str] = set()
                previous: str | None = None
                for label in labels:
                    if label != previous and label in seen:
                        _fail("HERMITE_NODES_NOT_GROUPED", node_id)
                    seen.add(label)
                    previous = label
            parsed_nodes = [self._parse(label, "NODE_EXPRESSION_INVALID") for label in labels]
            parameter = parameters[latent.parameters[0]]

            def divided_difference(start: int, stop: int) -> sympy.Expr:
                subset = labels[start:stop]
                if len(set(subset)) == 1:
                    order = stop - start - 1
                    derivative = sympy.diff(expression, parameter, order)
                    return derivative.xreplace({parameter: parsed_nodes[start]}) / math.factorial(order)
                left = divided_difference(start, stop - 1)
                right = divided_difference(start + 1, stop)
                return (right - left) / (parsed_nodes[stop - 1] - parsed_nodes[start])

            return divided_difference(0, len(labels))

        if kind == "RECURRENCE":
            if len(inputs) > 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            _latent, latent_expression, parameters = self._latent(operator)
            base = self._parse(args.get("base"), "RECURRENCE_BASE_INVALID")
            step = self._parse(args.get("step"), "RECURRENCE_STEP_INVALID")
            form = args.get("form")
            if inputs:
                base_expression = inputs[0]
                external = self._parse(args.get("parameter"), "RECURRENCE_PARAMETER_INVALID")
                if not isinstance(external, sympy.Symbol):
                    _fail("RECURRENCE_PARAMETER_INVALID", operator.operator_id)
                shifted = base_expression.xreplace({external: external + step})
            else:
                parameter = self._parameter(operator, args.get("parameter"), parameters)
                base_expression = latent_expression.xreplace({parameter: base})
                shifted = latent_expression.xreplace({parameter: base + step})
            if form == "FORWARD_DIFFERENCE":
                return shifted - base_expression
            if form == "SHIFTED_VALUE":
                return shifted
            _fail("RECURRENCE_FORM_INVALID", operator.operator_id)

        if kind in {"LINEAR_COMBINATION", "BASIS_RECONSTRUCT"}:
            if not inputs:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            coefficients = args.get("coefficients")
            if not isinstance(coefficients, list) or len(coefficients) != len(inputs):
                _fail("LINEAR_COEFFICIENTS_INVALID", operator.operator_id)
            parsed_coefficients = [
                self._parse(value, "LINEAR_COEFFICIENT_INVALID")
                for value in coefficients
            ]
            constant = self._parse(args.get("constant", "0"), "LINEAR_CONSTANT_INVALID")
            return sympy.Add(
                constant,
                *(coefficient * term for coefficient, term in zip(parsed_coefficients, inputs)),
            )

        if kind == "BASIS_PROJECT":
            if len(inputs) != 1:
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            basis = self._parse(args.get("basis"), "BASIS_EXPRESSION_INVALID")
            coefficient = self._parse(args.get("coefficient", "1"), "BASIS_COEFFICIENT_INVALID")
            return coefficient * inputs[0] * basis

        if kind == "COMPOSE":
            latent, expression, parameters = self._latent(operator)
            if len(inputs) != len(latent.parameters):
                _fail("OPERATOR_ARITY_INVALID", operator.operator_id)
            replacements = {
                parameters[name]: value
                for name, value in zip(latent.parameters, inputs)
            }
            return expression.xreplace(replacements)

        _fail("OPERATOR_UNKNOWN", kind)

    def obligations(self) -> tuple[CompiledObligation, ...]:
        assignments = {item.member_id: item for item in self.program.member_assignments}
        obligation_members = {
            item.member_id
            for item in self.program.obligations
            if item.member_id is not None
        }
        missing_obligations = set(assignments) - obligation_members
        if missing_obligations:
            _fail(
                "OBLIGATION_FOR_ASSIGNMENT_MISSING",
                sorted(missing_obligations)[0],
            )
        result: list[CompiledObligation] = []
        bound_names = {
            parameter
            for latent in self.program.latent_objects
            for parameter in latent.parameters
        }
        for obligation in self.program.obligations:
            if obligation.member_id is None:
                _fail("OBLIGATION_MEMBER_MISSING", obligation.obligation_id)
            if obligation.output is None:
                _fail("OBLIGATION_OUTPUT_MISSING", obligation.obligation_id)
            if obligation.member_id not in assignments:
                _fail("OBLIGATION_ASSIGNMENT_UNKNOWN", obligation.member_id)
            assignment = assignments[obligation.member_id]
            if assignment.output != obligation.output:
                _fail("OBLIGATION_ASSIGNMENT_MISMATCH", obligation.obligation_id)
            dependency_ids = tuple(
                item.operator_id
                for item in _dependency_closure(self.program, assignment.output)
            )
            if assignment.operator_ids != dependency_ids:
                _fail("MEMBER_RECONSTRUCTION_MISMATCH", assignment.member_id)
            if obligation.output not in self.outputs:
                _fail("OBLIGATION_OUTPUT_UNKNOWN", obligation.output)
            candidate = self.outputs[obligation.output]
            free_names = {str(symbol) for symbol in candidate.free_symbols}
            unresolved = free_names & bound_names
            if unresolved:
                _fail("UNBOUND_LATENT_PARAMETER", sorted(unresolved)[0])
            source = next(
                item for item in self.program.source_members
                if item.member_id == obligation.member_id
            )
            current = self.source_records[obligation.member_id]
            result.append(CompiledObligation(
                obligation_id=obligation.obligation_id,
                member_id=obligation.member_id,
                current_path=source.path,
                current_sha256=source.sha256,
                current_expression=current.text,
                candidate_expression=str(candidate),
                required=obligation.required,
            ))
        if not result:
            _fail("OBLIGATIONS_MISSING")
        return tuple(result)


def _dependency_closure(program: RepresentationProgram, output: str) -> tuple[Operator, ...]:
    by_output = {
        item.output: item for item in program.operators if item.output is not None
    }
    found: list[Operator] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in by_output:
            return
        seen.add(name)
        operator = by_output[name]
        for dependency in operator.inputs:
            visit(dependency)
        found.append(operator)

    visit(output)
    return tuple(found)


def is_tautological(
    program: RepresentationProgram,
    context: CompileContext,
) -> bool:
    """Detect independent VALUE-self wrappers using exact source text.

    This is intentionally an IR-level diagnostic, not a proof procedure.
    Any parse/hash problem fails closed by returning ``False`` to the caller;
    ``compile_program`` reports the actual compile failure separately.
    """
    try:
        constructor = _Constructor(program, context)
        constructor.validate_common()
    except _CompileFailure:
        return False
    latent_by_id = {item.latent_id: item for item in program.latent_objects}
    uses: dict[str, set[str]] = {}
    for assignment in program.member_assignments:
        if assignment.output is None:
            return False
        closure = _dependency_closure(program, assignment.output)
        if len(closure) != 1 or closure[0].operator != "VALUE":
            return False
        operator = closure[0]
        if operator.latent_id is None:
            return False
        latent = latent_by_id[operator.latent_id]
        source = constructor.source_records[assignment.member_id]
        if latent.expression.strip() != source.text.strip():
            return False
        uses.setdefault(operator.latent_id, set()).add(assignment.member_id)
    return bool(program.member_assignments) and not any(
        len(member_ids) >= 2 for member_ids in uses.values()
    )


def compile_program(
    program: RepresentationProgram,
    context: CompileContext,
) -> CompilationResult:
    """Compile a typed program; every exceptional path is COMPILE_FAILURE."""
    try:
        program_id = canonical_program_hash(program)
    except Exception:
        return CompilationResult(
            status="COMPILE_FAILURE",
            program_id="UNHASHABLE",
            failure_codes=("CANONICALIZATION_FAILURE",),
        )
    try:
        constructor = _Constructor(program, context)
        if (
            program.declared_program_id is not None
            and program.declared_program_id != program_id
        ):
            _fail("PROGRAM_ID_MISMATCH")
        constructor.validate_common()
        constructor.execute()
        obligations = constructor.obligations()
        tautological = is_tautological(program, context)
        return CompilationResult(
            status="COMPILED",
            program_id=program_id,
            obligations=obligations,
            tautological=tautological,
        )
    except _CompileFailure as exc:
        return CompilationResult(
            status="COMPILE_FAILURE",
            program_id=program_id,
            failure_codes=(exc.code,),
        )
    except Exception as exc:
        # The stable outer code avoids leaking implementation exceptions into
        # the scientific status taxonomy while still failing closed.
        return CompilationResult(
            status="COMPILE_FAILURE",
            program_id=program_id,
            failure_codes=(f"INTERNAL_CONSTRUCTOR_FAILURE:{type(exc).__name__}",),
        )
