"""Deterministic structural duplicate and target-leakage audit.

The audit deliberately has no access to a gold representation program.  It
compares source-facing identity fields (formulae, source catalogs, titles and
citations) and checks the separately defined proposer-visible projection for
representation-language leakage.  Similarity is review evidence only: this
module never mutates a dossier and never emits an admission/rejection verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


POLICY_VERSION = "RPS_DUPLICATE_LEAKAGE_AUDIT_V1"

EXACT_DUPLICATE = "EXACT_DUPLICATE_IDENTITY_RISK"
RENAMED_DUPLICATE = "RENAMED_IDENTITY_RISK"
NEAR_DUPLICATE = "NEAR_DUPLICATE_IDENTITY_RISK"
HISTORICAL_ID = "HISTORICAL_ID_REFERENCE"
SEALED_GUO = "SEALED_GUO_REFERENCE"
GRAMMAR_SYNTAX = "GRAMMAR_SYNTAX_LEAKAGE"
OPERATOR_NAME = "OPERATOR_NAME_LEAKAGE"
HIDDEN_MEMBER_ROLE = "HIDDEN_MEMBER_ROLE_LEAKAGE"
TRIVIAL_CSE = "TRIVIAL_CSE"
FIRST_ORDER_LGG_ONLY = "FIRST_ORDER_LGG_ONLY"

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Deliberately conservative.  G#### is also the ordinary catalog namespace, so
# an isolated G0013/G0016 is not enough; the sealed hop pair or Guo name is.
SEALED_GUO_NAMES = (
    "guo",
    "sigma_abc",
    "sigma abc",
    "nc-guo-sigma-abc",
)
SEALED_GUO_HOP = ("g0016", "g0013")

EXPLICIT_GRAMMAR_PATTERNS = (
    r"\b(?:NEWTON_DD|HERMITE_DD|BASIS_PROJECT|BASIS_RECONSTRUCT)\b",
    r"\b(?:CREATE_LATENT|ADD_MEMBER|GROUP_MEMBERS|ADD_PARAMETER)\b",
    r"\b(?:SUBSTITUTE_PARAMETER|ADD_DERIVATIVE|ADD_NEWTON_DD)\b",
    r"\b(?:ADD_REPEATED_NODE|ADD_HERMITE_DD|ADD_RECURRENCE)\b",
    r"\b(?:ADD_PERMUTATION|ADD_LINEAR_COMBINATION|CREATE_BASIS)\b",
    r"\b(?:RECONSTRUCT_FROM_BASIS|REMOVE_REDUNDANT_OBJECT)\b",
    r"\bNODES\s*\[",
    r"\b(?:gold program|gold operator|target representation(?: type)?)\b",
)

# Natural mathematical names may be legitimate source terminology.  They are
# therefore MEDIUM review findings, distinct from literal grammar/action syntax.
NATURAL_OPERATOR_PATTERNS = (
    ("HERMITE", r"\bhermite(?:\s+(?:divided difference|interpol(?:ant|ation)))?\b"),
    ("NEWTON_DD", r"\bnewton(?:\s+(?:divided difference|difference quotient|quotient))\b"),
    ("DIVIDED_DIFFERENCE", r"\bdivided difference\b"),
    ("RECURRENCE", r"\brecurrence\b"),
    ("BASIS_RECONSTRUCT", r"\b(?:basis reconstruction|reconstruct(?:ion)? from (?:a )?basis)\b"),
    ("BASIS_PROJECT", r"\bbasis project(?:ion)?\b"),
    ("REPEATED_NODE", r"\brepeated[- ]node\b"),
)

ROLE_KEY_RE = re.compile(
    r"(?:^|_)(?:gold|target|role|hidden_role|member_role|operator_sequence|"
    r"representation_type|latent_assignment)(?:$|_)",
    re.I,
)
ROLE_VALUE_RE = re.compile(
    r"\b(?:target_expression|gold_member|master_member|diagonal_derivative|"
    r"repeated_node_member|basis_seed|latent_generator)\b",
    re.I,
)

FORMULA_FIELDS = (
    "expression_sketch",
    "current",
    "source_expressions",
    "expressions",
)
PROPOSER_FIELDS = ("title", "expression_sketch", "proposer_view", "source_catalog", "catalog")

STOPWORDS = frozenset(
    "a an and are as at be by can case do does for from has have if in into is it "
    "let may not of on one or same that the their then this to under using valid via "
    "was when where which with without write written".split()
)

KNOWN_FORMULA_WORDS = frozenset(
    "abs add adjoint cos cosh derivative det exp gamma im integral inverse log matrix "
    "mul polygamma product re sin sinh sqrt sum tan tanh trace transpose zeta".split()
)
GREEK_VARIABLES = frozenset(
    "alpha beta chi delta epsilon eta gamma kappa lambda lam mu nu omega phi psi rho "
    "sigma tau theta xi zeta".split()
)


@dataclass(frozen=True)
class CorpusDocument:
    document_id: str
    path: str
    partition: str
    title: str
    formulas: tuple[str, ...]
    identity_text: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    evidence: dict[str, Any]
    recommendation: str = "MANUAL_REVIEW"
    auto_reject: bool = False


def _json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _walk_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key in sorted(value, key=str):
            yield from _walk_strings(value[key])
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _flatten_field(value: Any) -> list[str]:
    return [part.strip() for part in _walk_strings(value) if part.strip()]


def source_formulas(payload: dict[str, Any]) -> tuple[str, ...]:
    """Return source-facing formula/catalog text, excluding target/gold fields."""
    out: list[str] = []
    for field in FORMULA_FIELDS:
        out.extend(_flatten_field(payload.get(field)))
    for field in ("catalog", "source_catalog", "members"):
        value = payload.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for key in ("text", "expression", "source", "formula"):
                        if isinstance(item.get(key), str):
                            out.append(item[key].strip())
                elif isinstance(item, str):
                    out.append(item.strip())
        elif isinstance(value, dict):
            for key in sorted(value, key=str):
                item = value[key]
                if isinstance(item, str):
                    out.append(item.strip())
                elif isinstance(item, dict):
                    for text_key in ("text", "expression", "source", "formula"):
                        if isinstance(item.get(text_key), str):
                            out.append(item[text_key].strip())
    expanded: list[str] = []
    for item in out:
        if not item:
            continue
        expanded.append(item)
        expanded.extend(_equation_fragments(item))
    return tuple(dict.fromkeys(item for item in expanded if item))


def _equation_fragments(text: str) -> list[str]:
    """Expose equation clauses without interpreting or simplifying them."""
    clauses = re.split(r"(?:\n+|;|\.\s+(?=[A-Z]))", text)
    out: list[str] = []
    for clause in clauses:
        clause = clause.strip(" .")
        if len(clause) < 12 or "=" not in clause:
            continue
        if ":" in clause:
            suffix = clause.rsplit(":", 1)[1].strip()
            if "=" in suffix and len(suffix) >= 8:
                clause = suffix
        else:
            equals_at = clause.find("=")
            prefixes = list(re.finditer(r"\b[A-Za-z_][A-Za-z_0-9]*\s*\(", clause[:equals_at]))
            if prefixes:
                clause = clause[prefixes[0].start() :]
        out.append(clause)
    return out


def proposer_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the explicit proposer view, or the frozen source-field fallback."""
    if "proposer_view" in payload:
        return {"proposer_view": payload.get("proposer_view")}
    return {key: payload[key] for key in PROPOSER_FIELDS if key in payload and key != "proposer_view"}


def _unicode_normalize(text: str) -> str:
    table = str.maketrans(
        {
            "−": "-",
            "–": "-",
            "—": "-",
            "×": "*",
            "·": "*",
            "÷": "/",
            "λ": "lambda",
            "μ": "mu",
            "ν": "nu",
            "ω": "omega",
            "ξ": "xi",
            "ε": "epsilon",
            "θ": "theta",
            "φ": "phi",
            "ψ": "psi",
            "π": "pi",
            "Σ": "sum",
            "∑": "sum",
            "∞": "oo",
            "≠": "!=",
            "≤": "<=",
            "≥": ">=",
            "→": "->",
            "↔": "<->",
        }
    )
    return unicodedata.normalize("NFKC", text).translate(table)


def strict_normalize(text: str) -> str:
    text = _unicode_normalize(text).casefold()
    return re.sub(r"\s+", "", text)


TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z_0-9]*|(?:\d+(?:\.\d+)?)|==|!=|<=|>=|->|\*\*|[+\-*/^=(),\[\]{}]"
)


def formula_tokens(text: str) -> list[str]:
    return [tok.casefold() for tok in TOKEN_RE.findall(_unicode_normalize(text))]


def _is_variable_token(token: str) -> bool:
    if token in KNOWN_FORMULA_WORDS:
        return False
    if token in GREEK_VARIABLES:
        return True
    if len(token) == 1 and token.isalpha():
        return True
    if re.fullmatch(r"[a-z]+_?\d+", token):
        return True
    if re.fullmatch(r"[a-z]_[a-z0-9]+", token):
        return True
    return False


def alpha_normalize(text: str) -> tuple[str, ...]:
    """Normalize symbol names while preserving mathematical heads and syntax."""
    mapping: dict[str, str] = {}
    out: list[str] = []
    for token in formula_tokens(text):
        if _is_variable_token(token):
            if token not in mapping:
                mapping[token] = f"v{len(mapping)}"
            out.append(mapping[token])
        else:
            out.append(token)
    return tuple(out)


WORD_RE = re.compile(r"[a-z][a-z0-9_]{1,}")


def content_words(text: str) -> frozenset[str]:
    words = WORD_RE.findall(_unicode_normalize(text).casefold())
    return frozenset(word for word in words if word not in STOPWORDS and not word.isdigit())


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _formula_similarity(left: Sequence[str], right: Sequence[str]) -> float:
    best = 0.0
    for a in left:
        at = alpha_normalize(a)
        if len(at) < 6:
            continue
        for b in right:
            bt = alpha_normalize(b)
            if len(bt) < 6:
                continue
            ratio = SequenceMatcher(a=at, b=bt, autojunk=False).ratio()
            best = max(best, ratio)
    return best


SOURCE_ID_PATTERNS = (
    re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+", re.I),
    re.compile(r"\barxiv\s*:\s*[a-z.-]*/?\d{4}\.\d{4,5}\b", re.I),
    re.compile(r"\bdlmf\s+\d+(?:\.\d+){1,3}(?:\.e?\d+)?\b", re.I),
)


def source_identifiers(payload: dict[str, Any]) -> tuple[str, ...]:
    bits: list[str] = []
    for key in ("public_source", "source_provenance"):
        bits.extend(_flatten_field(payload.get(key)))
    contract = payload.get("assumption_contract")
    if isinstance(contract, dict):
        bits.extend(_flatten_field(contract.get("source_provenance")))
    blob = "\n".join(bits)
    found: set[str] = set()
    for pattern in SOURCE_ID_PATTERNS:
        for match in pattern.findall(blob):
            found.add(match.casefold().rstrip(".,;"))
    for url in re.findall(r"https?://[^\s)\]}>,;]+", blob, re.I):
        found.add(url.casefold().rstrip("."))
    return tuple(sorted(found))


def _identity_text(payload: dict[str, Any], formulas: Sequence[str]) -> str:
    title = payload.get("title")
    bits = [title] if isinstance(title, str) else []
    bits.extend(formulas)
    return "\n".join(bits)


def _partition_for(path: Path, partition_map: dict[str, str]) -> str:
    parts = set(path.parts)
    name = path.stem
    if name in partition_map:
        return partition_map[name]
    if "assumption_complete_representation" in parts:
        return "HISTORICAL_DIAGNOSTIC"
    if "bench" in parts or "benchmark" in parts or "benchmarks" in parts:
        return "PREVIOUS_BENCHMARK"
    return "PREVIOUS_CASE_CORPUS"


def _manifest_partition_map(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    ac = root / "research" / "assumption_complete_representation"
    dev_path = ac / "DEV_MANIFEST.json"
    if dev_path.is_file():
        payload = _json(dev_path)
        for task in payload.get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("case_id"), str):
                out[task["case_id"]] = "AC_DEV"
    test_path = ac / "TEST_MANIFEST.json"
    if test_path.is_file():
        payload = _json(test_path)
        for key in ("HEADLINE", "CORE_COMPARABLE", "DUPLICATE_CONTROL", "CHALLENGE"):
            for case_id in payload.get(key, []):
                if isinstance(case_id, str):
                    out.setdefault(case_id, f"AC_{key}")
    return out


def discover_new_dossiers(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    cases = root / "research" / "representation_program_search" / "cases"
    rows: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(cases.glob("**/*.json")):
        if path.name == "index.json":
            continue
        payload = _json(path)
        if isinstance(payload, dict) and isinstance(payload.get("case_id"), str):
            rows.append((path, payload))
    return rows


def discover_reference_corpus(root: Path) -> list[CorpusDocument]:
    """Load previous case/benchmark source objects, never run or open Guo data."""
    partition_map = _manifest_partition_map(root)
    research = root / "research"
    current = research / "representation_program_search"
    docs: list[CorpusDocument] = []
    for path in sorted(research.glob("**/*.json")):
        if current in path.parents:
            continue
        parts = set(path.parts)
        if not ({"cases", "bench", "benchmark", "benchmarks"} & parts):
            continue
        if any(part in {"runs", "results", "final", "audit", "reviews"} for part in path.parts):
            continue
        try:
            payload = _json(path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        doc_id = payload.get("case_id", payload.get("id", payload.get("task_id")))
        if not isinstance(doc_id, str) or not doc_id.strip():
            continue
        formulas = source_formulas(payload)
        title = payload.get("title", "")
        title = title if isinstance(title, str) else ""
        if not formulas and not title:
            continue
        docs.append(
            CorpusDocument(
                document_id=doc_id,
                path=str(path.relative_to(root)),
                partition=_partition_for(path, partition_map),
                title=title,
                formulas=formulas,
                identity_text=_identity_text(payload, formulas),
                source_ids=source_identifiers(payload),
            )
        )
    return docs


def historical_ids(root: Path, references: Sequence[CorpusDocument]) -> tuple[str, ...]:
    """Union corpus ids with AC manifest and Historical Diagnostic ids."""
    ids = {doc.document_id for doc in references}
    ids.update(_manifest_partition_map(root))
    hist = root / "research" / "representation_program_search" / "HISTORICAL_DIAGNOSTIC.md"
    if hist.is_file():
        text = hist.read_text(encoding="utf-8")
        ids.update(
            re.findall(
                r"\b(?:mp|sciml|thermal|ac-[rt]|nc)-[a-z0-9][a-z0-9-]*\b",
                text.casefold(),
            )
        )
    return tuple(sorted(ids))


def _comparison(new_payload: dict[str, Any], ref: CorpusDocument) -> dict[str, Any]:
    formulas = source_formulas(new_payload)
    exact_pairs: list[tuple[str, str]] = []
    renamed_pairs: list[tuple[str, str]] = []
    for left in formulas:
        ln = strict_normalize(left)
        la = alpha_normalize(left)
        for right in ref.formulas:
            rn = strict_normalize(right)
            ra = alpha_normalize(right)
            # Short identities such as phi_0(z)=exp(z) are common primitives,
            # not enough on their own to call two cases exact duplicates.
            if len(ln) >= 16 and len(la) >= 12 and ln == rn:
                exact_pairs.append((left, right))
            elif len(la) >= 8 and la == ra and ln != rn:
                renamed_pairs.append((left, right))
    identity = _identity_text(new_payload, formulas)
    formula_score = _formula_similarity(formulas, ref.formulas)
    content_score = _jaccard(content_words(identity), content_words(ref.identity_text))
    new_source_ids = source_identifiers(new_payload)
    source_score = _jaccard(new_source_ids, ref.source_ids)
    weighted = 0.55 * formula_score + 0.30 * content_score + 0.15 * source_score
    return {
        "reference_id": ref.document_id,
        "reference_path": ref.path,
        "reference_partition": ref.partition,
        "exact": bool(exact_pairs),
        "renamed": bool(renamed_pairs),
        "formula_similarity": round(formula_score, 6),
        "content_jaccard": round(content_score, 6),
        "source_id_jaccard": round(source_score, 6),
        "weighted_similarity": round(weighted, 6),
        "shared_source_ids": sorted(set(new_source_ids) & set(ref.source_ids)),
        "projection": "SOURCE_IDENTITY_FIELDS_ONLY",
        "matched_fragment_sha256": [
            {
                "new": hashlib.sha256(pair[0].encode()).hexdigest(),
                "reference": hashlib.sha256(pair[1].encode()).hexdigest(),
            }
            for pair in (exact_pairs or renamed_pairs)[:3]
        ],
        "matched_fragment_preview": [
            {
                "new": pair[0][:240],
                "reference": pair[1][:240],
                "truncated": len(pair[0]) > 240 or len(pair[1]) > 240,
            }
            for pair in (exact_pairs or renamed_pairs)[:3]
        ],
    }


def _explicit_historical_mentions(payload: dict[str, Any], ids: Sequence[str]) -> list[str]:
    # Internal "distinct from old-X" notes are audit evidence, not ancestry and
    # not proposer-visible.  Only explicit ancestry fields and public labels
    # trigger this rule.
    fields = [payload.get(key) for key in ("case_id", "title", "historical_parent", "renamed_from", "historical_ids")]
    blob = "\n".join(_flatten_field(fields)).casefold()
    matches: list[str] = []
    for case_id in ids:
        if re.search(r"(?<![a-z0-9])" + re.escape(case_id.casefold()) + r"(?![a-z0-9])", blob):
            if case_id != str(payload.get("case_id", "")).casefold():
                matches.append(case_id)
    return sorted(set(matches))


def _sealed_guo_evidence(payload: dict[str, Any]) -> list[str]:
    projection = proposer_projection(payload)
    meta = {key: payload.get(key) for key in ("case_id", "title", "historical_parent", "historical_ids")}
    blob = "\n".join(_flatten_field([projection, meta])).casefold()
    found = [name for name in SEALED_GUO_NAMES if name in blob]
    if all(identifier in blob for identifier in SEALED_GUO_HOP):
        found.append("G0016->G0013")
    if payload.get("is_guo") is True:
        found.append("is_guo=true")
    return sorted(set(found))


def _leakage_findings(payload: dict[str, Any]) -> list[Finding]:
    projection = proposer_projection(payload)
    blob = "\n".join(_flatten_field(projection))
    findings: list[Finding] = []
    explicit = sorted(
        {match.group(0) for pattern in EXPLICIT_GRAMMAR_PATTERNS for match in re.finditer(pattern, blob, re.I)}
    )
    if explicit:
        findings.append(
            Finding(
                GRAMMAR_SYNTAX,
                "HIGH",
                {"matches": explicit, "projection": "explicit" if "proposer_view" in payload else "fallback_source_fields"},
            )
        )
    natural: list[dict[str, str]] = []
    for operator, pattern in NATURAL_OPERATOR_PATTERNS:
        for match in re.finditer(pattern, blob, re.I):
            natural.append({"operator": operator, "match": match.group(0)})
    if natural:
        unique = sorted({(row["operator"], row["match"].casefold()) for row in natural})
        findings.append(
            Finding(
                OPERATOR_NAME,
                "MEDIUM",
                {
                    "matches": [{"operator": operator, "text": text} for operator, text in unique],
                    "note": "Natural source terminology; review packaging, not scientific validity.",
                },
            )
        )
    role_keys: list[str] = []
    role_values: list[str] = []

    def visit(value: Any, dotted: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value, key=str):
                child = f"{dotted}.{key}" if dotted else str(key)
                if ROLE_KEY_RE.search(str(key)):
                    role_keys.append(child)
                visit(value[key], child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{dotted}[{index}]")
        elif isinstance(value, str):
            role_values.extend(match.group(0) for match in ROLE_VALUE_RE.finditer(value))

    visit(projection, "")
    if role_keys or role_values:
        findings.append(
            Finding(
                HIDDEN_MEMBER_ROLE,
                "HIGH",
                {"keys": sorted(set(role_keys)), "role_values": sorted(set(role_values))},
            )
        )
    return findings


def _split_top(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        if depth == 0 and text.startswith(separator, index):
            parts.append("".join(current).strip())
            current = []
            index += len(separator)
            continue
        current.append(char)
        index += 1
    parts.append("".join(current).strip())
    return parts


def is_trivial_cse(sketch: str) -> bool:
    text = sketch.strip()
    if not text:
        return False
    for head in ("Add", "Mul"):
        if text.startswith(head + "(") and text.endswith(")"):
            args = _split_top(text[len(head) + 1 : -1], ",")
            cleaned = [strict_normalize(arg) for arg in args if arg.strip()]
            return len(cleaned) >= 2 and max(Counter(cleaned).values()) >= 2
    # Infix screening is intentionally limited to a short standalone formula.
    # Long scientific sketches contain many unrelated top-level plus signs and
    # are not evidence of a single repeated-term CSE.
    if len(text) > 256 or "\n" in text or re.search(r"\b(?:where|with|for|let|catalog)\b", text, re.I):
        return False
    for separator in ("+", "*"):
        parts = _split_top(text, separator)
        cleaned = [strict_normalize(part) for part in parts if part.strip()]
        if len(cleaned) >= 2 and max(Counter(cleaned).values()) >= 2:
            return True
    return False


def is_first_order_lgg_only(payload: dict[str, Any]) -> bool:
    ladder = str(payload.get("proposed_ladder", "")).casefold()
    latent = str(payload.get("latent_structure", "")).casefold()
    notes = str(payload.get("notes", "")).casefold()
    explicit = " ".join((latent, notes))
    lgg_named = bool(
        re.search(r"\b(?:first[- ]order\s+)?lgg\b", explicit)
        or "least-general generalization" in explicit
        or "least general generalization" in explicit
        or "first-order anti-unification" in explicit
    )
    shallow_ladder = ladder.startswith("r1_")
    return lgg_named or shallow_ladder


def audit_case(
    payload: dict[str, Any],
    references: Sequence[CorpusDocument],
    forbidden_ids: Sequence[str],
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    case_id = str(payload.get("case_id", ""))
    findings = _leakage_findings(payload)
    comparisons = [_comparison(payload, reference) for reference in references]
    comparisons.sort(
        key=lambda row: (
            not row["exact"],
            not row["renamed"],
            -row["weighted_similarity"],
            row["reference_id"],
            row["reference_path"],
        )
    )
    for row in comparisons:
        if row["exact"]:
            findings.append(Finding(EXACT_DUPLICATE, "HIGH", row))
        elif row["renamed"]:
            findings.append(Finding(RENAMED_DUPLICATE, "HIGH", row))
        elif (
            row["weighted_similarity"] >= 0.58
            or (row["formula_similarity"] >= 0.645 and row["content_jaccard"] >= 0.15)
        ):
            findings.append(Finding(NEAR_DUPLICATE, "MEDIUM", row))
    mentioned = _explicit_historical_mentions(payload, forbidden_ids)
    if mentioned:
        findings.append(
            Finding(
                HISTORICAL_ID,
                "HIGH",
                {
                    "historical_ids": mentioned,
                    "projection": ["case_id", "title", "historical_parent", "renamed_from", "historical_ids"],
                },
            )
        )
    guo = _sealed_guo_evidence(payload)
    if guo:
        findings.append(
            Finding(
                SEALED_GUO,
                "CRITICAL",
                {
                    "matches": guo,
                    "projection": ["proposer_projection", "case_id", "title", "historical_parent", "historical_ids", "is_guo=true"],
                },
            )
        )
    sketch = payload.get("expression_sketch")
    if isinstance(sketch, str) and is_trivial_cse(sketch):
        findings.append(
            Finding(
                TRIVIAL_CSE,
                "HIGH",
                {
                    "expression_sha256": hashlib.sha256(sketch.encode()).hexdigest(),
                    "projection": "expression_sketch",
                },
            )
        )
    if is_first_order_lgg_only(payload):
        findings.append(
            Finding(
                FIRST_ORDER_LGG_ONLY,
                "HIGH",
                {
                    "proposed_ladder": payload.get("proposed_ladder", ""),
                    "basis": "declared metadata only",
                    "projection": ["latent_structure", "proposed_ladder", "notes"],
                },
            )
        )
    deduped: dict[str, Finding] = {}
    for finding in findings:
        key = json.dumps(asdict(finding), sort_keys=True, ensure_ascii=False)
        deduped[key] = finding
    ordered = sorted(
        deduped.values(),
        key=lambda item: (SEVERITY_ORDER[item.severity], item.code, json.dumps(item.evidence, sort_keys=True)),
    )
    rejected_control = payload.get("rejected") is True or payload.get("admitted") is False
    return {
        "case_id": case_id,
        "path": payload.get("_audit_path", ""),
        "is_negative_control": rejected_control,
        "proposer_projection": "explicit" if "proposer_view" in payload else "fallback_source_fields",
        "findings": [asdict(item) for item in ordered],
        "highest_severity": ordered[0].severity if ordered else "NONE",
        "requires_manual_review": bool(ordered) and not rejected_control,
        "admission_decision": None,
        "top_comparisons": comparisons[:top_k],
    }


def audit_repository(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    new_rows = discover_new_dossiers(root)
    references = discover_reference_corpus(root)
    forbidden = historical_ids(root, references)
    cases: list[dict[str, Any]] = []
    for path, original in new_rows:
        payload = dict(original)
        payload["_audit_path"] = str(path.relative_to(root))
        cases.append(audit_case(payload, references, forbidden))
    cases.sort(key=lambda row: row["case_id"])
    counts = Counter(
        finding["code"]
        for case in cases
        for finding in case["findings"]
    )
    severity = Counter(
        finding["severity"]
        for case in cases
        for finding in case["findings"]
    )
    scientific = [case for case in cases if not case["is_negative_control"]]
    flagged = [case["case_id"] for case in scientific if case["findings"]]
    return {
        "schema": POLICY_VERSION,
        "gold_fields_used": False,
        "mutates_cases": False,
        "auto_rejects_similarity": False,
        "similarity_policy": {
            "weighted_similarity": 0.58,
            "formula_similarity_with_content": [0.645, 0.15],
            "citation_overlap_alone": "NOT_A_DUPLICATE_FINDING",
        },
        "new_dossier_count": len(cases),
        "scientific_candidate_count": len(scientific),
        "negative_control_count": len(cases) - len(scientific),
        "reference_document_count": len(references),
        "reference_partitions": dict(sorted(Counter(doc.partition for doc in references).items())),
        "finding_counts": dict(sorted(counts.items())),
        "severity_counts": dict(sorted(severity.items())),
        "scientific_cases_requiring_review": flagged,
        "cases": cases,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Representation Program Search — Duplicate and Leakage Audit",
        "",
        f"Policy: `{report['schema']}`.",
        "",
        "This is a deterministic, gold-free screening report. Similarity is review evidence; "
        "it is never an automatic rejection or scientific verdict.",
        "",
        "## Coverage",
        "",
        f"- New dossiers: {report['new_dossier_count']} "
        f"({report['scientific_candidate_count']} scientific, {report['negative_control_count']} controls)",
        f"- Previous reference documents: {report['reference_document_count']}",
        f"- Scientific cases requiring review: {len(report['scientific_cases_requiring_review'])}",
        "",
        "## Scientific-case findings",
        "",
    ]
    scientific = [case for case in report["cases"] if not case["is_negative_control"] and case["findings"]]
    if not scientific:
        lines.append("No scientific case crossed a frozen audit rule or similarity threshold.")
    for case in scientific:
        lines.extend((f"### {case['case_id']} — {case['highest_severity']}", ""))
        for finding in case["findings"]:
            evidence = finding["evidence"]
            if "reference_id" in evidence:
                detail = (
                    f"nearest `{evidence['reference_id']}` ({evidence['reference_partition']}), "
                    f"score={evidence['weighted_similarity']:.3f}"
                )
            elif "matches" in evidence:
                detail = ", ".join(str(item) for item in evidence["matches"])
            elif "historical_ids" in evidence:
                detail = ", ".join(evidence["historical_ids"])
            else:
                detail = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
            lines.append(f"- `{finding['code']}` ({finding['severity']}): {detail}")
        lines.append("")
    lines.extend(("## Negative-control calibration", ""))
    for case in report["cases"]:
        if not case["is_negative_control"]:
            continue
        codes = ", ".join(f"`{item['code']}`" for item in case["findings"]) or "no finding"
        lines.append(f"- `{case['case_id']}`: {codes}")
    lines.extend(
        (
            "",
            "## Interpretation boundary",
            "",
            "A flag means inspect the public task packaging. It does not mean the identity is duplicate, "
            "the case is invalid, or hidden gold was consulted. Exact certification and benchmark admission "
            "remain separate gates.",
            "",
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    report = audit_repository(args.root)
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
