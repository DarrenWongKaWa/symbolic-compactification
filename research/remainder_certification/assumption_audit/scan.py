"""Static assumption-leak scanner for remainder certification.

Hidden class-C/D hypotheses cannot emit CERTIFIED and cannot promote
hop ZERO. Source comments are not domain proofs. No LLM. D2 LOCKED.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    RemainderCertificate,
    UNKNOWN,
    validate_certificate,
)

# Patterns are regex, not the banned production tokens.
# Remainder Python must not contain the exact phrases the tests attack.
_RULES: tuple[tuple[str, str, str], ...] = (
    ("positive_beta", r"\bbeta\s*>\s*0\b", D_HUMAN_REQUIRED),
    ("positive_beta_unicode", r"β\s*>\s*0", D_HUMAN_REQUIRED),
    ("beta_positive_kw", r"(?:beta.*positive\s*=\s*True|positive\s*=\s*True.*beta)", D_HUMAN_REQUIRED),
    ("nonzero_beta", r"\bbeta\s*(?:!=|≠)\s*0\b", C_GENERICITY),
    ("assume_generic", r"assume\s+generic", C_GENERICITY),
    ("energy_arguments", r"energy\s+arguments", D_HUMAN_REQUIRED),
    ("half_plus_ie", r"1/2\s*\+\s*i\s*E\b", D_HUMAN_REQUIRED),
    ("generic_parameters", r"generic\s+parameters", C_GENERICITY),
    ("nonzero_gamma", r"\bgamma\s*(?:!=|≠)\s*0\b", C_GENERICITY),
    ("nonzero_gamma_unicode", r"γ\s*(?:!=|≠)\s*0", C_GENERICITY),
    ("real_mu_kw", r"symbols?\(\s*['\"]mu['\"][^)]*real\s*=\s*True", D_HUMAN_REQUIRED),
    ("real_mu_q", r"Q\.real\s*\(\s*mu\s*\)", D_HUMAN_REQUIRED),
    ("energy_diff_nonzero", r"energy\s+differences\s+nonzero", C_GENERICITY),
    ("not_polygamma_pole", r"not\s+(?:at\s+)?(?:a\s+)?polygamma\s+pole", C_GENERICITY),
    ("avoid_poles", r"generic\s+parameters\s+avoid\s+poles", C_GENERICITY),
    ("cauchy_m_finite", r"\bM\s*<\s*(?:∞|oo|inf(?:inity)?)\b", C_GENERICITY),
    ("sufficiently_small_t", r"sufficiently\s+small\s+t\b", C_GENERICITY),
    ("real_only_path", r"real[-_]only\s+path", D_HUMAN_REQUIRED),
)

_ENGINE_RULE_IDS = frozenset({"energy_arguments", "half_plus_ie"})

RULE_IDS = frozenset(rule_id for rule_id, _pat, _klass in _RULES)

_COMPILED: tuple[tuple[str, re.Pattern[str], str], ...] = tuple(
    (rule_id, re.compile(pat, re.IGNORECASE), klass) for rule_id, pat, klass in _RULES
)
_ENGINE_COMPILED = tuple(item for item in _COMPILED if item[0] in _ENGINE_RULE_IDS)


@dataclass(frozen=True)
class AssumptionLeak:
    """One silent class-C/D insertion in source or certificate text."""

    rule_id: str
    path: str
    line: int
    klass: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _rel(path: Path, root: Optional[Path]) -> str:
    base = (root if root is not None else _repo_root()).resolve()
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return str(path)


def _sort(leaks: Iterable[AssumptionLeak]) -> list[AssumptionLeak]:
    return sorted(leaks, key=lambda item: (item.path, item.line, item.rule_id, item.klass))


def scan_text(
    text: str,
    *,
    path: str = "<memory>",
    rules: Optional[Sequence[tuple[str, re.Pattern[str], str]]] = None,
) -> list[AssumptionLeak]:
    """Scan raw text, including comments. Empty text is clean."""
    compiled = _COMPILED if rules is None else tuple(rules)
    leaks: list[AssumptionLeak] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule_id, rx, klass in compiled:
            if rx.search(line):
                leaks.append(
                    AssumptionLeak(
                        rule_id=rule_id,
                        path=path,
                        line=lineno,
                        klass=klass,
                        snippet=line.strip()[:160],
                    )
                )
    return _sort(leaks)


def iter_remainder_python(root: Optional[Path] = None) -> list[Path]:
    """Production remainder_certification Python. Tests and pyc are skipped.

    Sibling packages (analysis/, cauchy/, …) may be absent.
    """
    base = Path(root) if root is not None else _repo_root()
    rc = base / "research" / "remainder_certification"
    if not rc.is_dir():
        return []
    out: list[Path] = []
    for path in sorted(rc.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if path.name.startswith("test_"):
            continue
        out.append(path)
    return out


def scan_remainder_python(root: Optional[Path] = None) -> list[AssumptionLeak]:
    """Scan remainder_certification production Python for silent hypotheses."""
    base = Path(root) if root is not None else _repo_root()
    leaks: list[AssumptionLeak] = []
    for path in iter_remainder_python(base):
        text = path.read_text(encoding="utf-8")
        leaks.extend(scan_text(text, path=_rel(path, base)))
    return _sort(leaks)


def engine_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else _repo_root()
    return base / "research" / "coefficient_laurent" / "engine.py"


def scan_engine(root: Optional[Path] = None, *, path: Optional[Path] = None) -> list[AssumptionLeak]:
    """Scan engine.py for the retracted energy-domain ZERO shortcut.

    Missing engine.py is clean: this auditor still passes on schema
    plus ASSUMPTION_POLICY.
    """
    base = Path(root) if root is not None else _repo_root()
    target = path if path is not None else engine_path(base)
    if not target.is_file():
        return []
    text = target.read_text(encoding="utf-8")
    return scan_text(text, path=_rel(target, base), rules=_ENGINE_COMPILED)


def scan_all(root: Optional[Path] = None) -> list[AssumptionLeak]:
    base = Path(root) if root is not None else _repo_root()
    return _sort(list(scan_remainder_python(base)) + list(scan_engine(base)))


def _declared_rule_ids(cert: RemainderCertificate) -> set[str]:
    declared: set[str] = set()
    for item in cert.assumptions_used:
        if not isinstance(item, dict):
            continue
        if item.get("class") not in (A_DECLARED, B_DERIVED):
            continue
        pred = str(item.get("predicate") or "")
        for leak in scan_text(pred, path="<declared>"):
            declared.add(leak.rule_id)
    return declared


def _cert_blobs(cert: RemainderCertificate) -> list[tuple[str, str]]:
    blobs: list[tuple[str, str]] = []
    for i, cond in enumerate(cert.domain_conditions):
        blobs.append((f"domain_conditions[{i}]", str(cond)))
    for name in (
        "note",
        "remainder_form",
        "required_small_t_condition",
        "bound",
        "distance_to_singularity",
    ):
        val = getattr(cert, name, "")
        if val:
            blobs.append((name, str(val)))
    if cert.analyticity_certificate:
        blobs.append(
            (
                "analyticity_certificate",
                json.dumps(cert.analyticity_certificate, sort_keys=True, default=str),
            )
        )
    for i, item in enumerate(cert.assumptions_used):
        if not isinstance(item, dict):
            blobs.append((f"assumptions_used[{i}]", str(item)))
            continue
        klass = item.get("class")
        if klass in (A_DECLARED, B_DERIVED, C_GENERICITY, D_HUMAN_REQUIRED):
            continue
        blobs.append(
            (
                f"assumptions_used[{i}]",
                json.dumps(item, sort_keys=True, default=str),
            )
        )
    return blobs


def certificate_silent_leaks(cert: RemainderCertificate) -> list[AssumptionLeak]:
    """Predicates in certificate text that are not class A/B declarations."""
    declared = _declared_rule_ids(cert)
    leaks: list[AssumptionLeak] = []
    for loc, text in _cert_blobs(cert):
        for leak in scan_text(text, path=f"<certificate:{loc}>"):
            if leak.rule_id in declared:
                continue
            leaks.append(leak)
    return _sort(leaks)


def _labeled_cd(cert: RemainderCertificate) -> bool:
    for item in cert.assumptions_used:
        if not isinstance(item, dict):
            continue
        if item.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED):
            return True
    return False


def has_hidden_hypotheses(
    *,
    leaks: Sequence[AssumptionLeak] = (),
    cert: Optional[RemainderCertificate] = None,
) -> bool:
    """True if source leaks or undeclared class-C/D hypotheses are present."""
    if leaks:
        return True
    if cert is None:
        return False
    if certificate_silent_leaks(cert):
        return True
    return _labeled_cd(cert)


def blocks_certified(
    leaks: Sequence[AssumptionLeak] = (),
    cert: Optional[RemainderCertificate] = None,
) -> bool:
    return has_hidden_hypotheses(leaks=leaks, cert=cert)


def blocks_hop_zero_promotion(
    leaks: Sequence[AssumptionLeak] = (),
    cert: Optional[RemainderCertificate] = None,
) -> bool:
    return has_hidden_hypotheses(leaks=leaks, cert=cert)


def audit_certificate(cert: RemainderCertificate) -> str:
    """validate_certificate plus silent-predicate detection. Never upgrades."""
    base = validate_certificate(cert)
    if base != CERTIFIED:
        return base
    if certificate_silent_leaks(cert):
        return ASSUMPTION_REQUIRED
    return CERTIFIED


def apply_assumption_gate(
    verdict: str,
    *,
    leaks: Sequence[AssumptionLeak] = (),
    cert: Optional[RemainderCertificate] = None,
) -> str:
    """Rewrite CERTIFIED/ZERO when hidden hypotheses are present.

    Remainder CERTIFIED is not hop ZERO. A hop remainder slot of ZERO
    becomes UNKNOWN; a remainder CERTIFIED becomes ASSUMPTION_REQUIRED.
    """
    if not has_hidden_hypotheses(leaks=leaks, cert=cert):
        return verdict
    if verdict == CERTIFIED:
        return ASSUMPTION_REQUIRED
    if verdict == HOP_ZERO:
        return UNKNOWN
    return verdict


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else _repo_root()
    leaks = scan_all(root)
    for leak in leaks:
        print(f"{leak.path}:{leak.line}:{leak.rule_id}:{leak.klass}:{leak.snippet}")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
