"""Exact source-byte authority for the frozen Structural Observation Layer.

The values are SHA-256 digests of file contents at git commit ``0a2905b``.
They are data, not a request to execute git or to trust an artifact's label.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from types import MappingProxyType

from research.representation_program_search.program_ir import canonical_json

SOL_AUTHORITY_SOURCE_SHA256 = MappingProxyType({
    "research/abstraction_invention/beyond/score.py": "194bdfcc24b18188dac90d5043bf76c934828ffecb81985c625c473650d6eea1",
    "research/abstraction_invention/prototype/antiunify.py": "2a2c1a385216060ef74b1968d58ec9e93e5be32cf1cad17d05ed6a80575b5f95",
    "src/symbolic_compactification/budgets.py": "9e972ff880ef907d8b015c96ec3bf6fe817a7ad35ec6368a9c7d64cc87bb95d9",
    "src/symbolic_compactification/models.py": "888850f2d51a8e651f0bf88ef9dd6ec9c3a073bf7d29ca8b2efb3578f93bbdac",
    "src/symbolic_compactification/observations/__init__.py": "8ad791f224388fa7d7f78a96204fbd4c7d7f4521c6ddd2ee76f5e44c0023fb53",
    "src/symbolic_compactification/observations/api.py": "b0e53e323b4d692c11297f77f092211ac7304b982d37b0c01022bb4a7451613b",
    "src/symbolic_compactification/observations/backends/__init__.py": "dc94016007b0def2476a944d6b0cba33f3e92110382311b73381cc8733fedc95",
    "src/symbolic_compactification/observations/backends/cadabra_backend.py": "a76c1485946cccf7786b30622d6b44c0cd30f11e2928c547b915684f03c67db1",
    "src/symbolic_compactification/observations/backends/egglog_backend.py": "505c834ba204f729891cc3ad1f5d383601f1fee94e620d52cff1b1b7e6e6568e",
    "src/symbolic_compactification/observations/backends/form_backend.py": "06b109e98afa7266c1e79974091b4f3cfbb880e84cb9eec58c70047c74a1ab13",
    "src/symbolic_compactification/observations/backends/lgg_backend.py": "60b50c51c73becbac1c1896a181eb0ef6537fdb9c31a436897e90aff5fde428b",
    "src/symbolic_compactification/observations/backends/matchpy_backend.py": "8ae42a3e211797d584af056dc05fd7e02a848c11f14307852889d5d496fa5996",
    "src/symbolic_compactification/observations/backends/sympy_backend.py": "9161826f01aa928aa44223bc4d0a1f0e8285305d22c532fcf840661bc8d362d3",
    "src/symbolic_compactification/observations/discovery.py": "e0bcd5bf6ac518a319537d674d6a37bffc19e0e5cf09ea9718f562f6137974f0",
    "src/symbolic_compactification/observations/graph.py": "39b038a9eb87dc273c2ca7a60569c4384c881724d247d5fc2dc246b5249fcbe0",
    "src/symbolic_compactification/observations/ir.py": "a50da52a707dd4c0baced2dbc6625f67fa8a0eb34cd1bd5ef54067d472ee1121",
    "src/symbolic_compactification/observations/leak.py": "972009b1805f6508dee928de1bfce865ae23e68ab73ac0922cbb3912d6dbfb44",
    "src/symbolic_compactification/observations/nodes.py": "de7906015ee05dd66178582d6d567577c154baf664e692459f4819348eaf9093",
    "src/symbolic_compactification/observations/packets.py": "f0be5fa75eaf933b73040b9011f91b93aaba1f8b84d4a4521ca9216a46ed2565",
    "src/symbolic_compactification/parser.py": "a61b31043bd23d6a3c08210ac0c173a6c2418bd3d44017db6f15ad5d7b5f11a9",
    "src/symbolic_compactification/structure.py": "5c788a580b04d4661cdaa6eedd7d7d1382d173132c4f65b641efff777b6f8fb9",
})
SOL_AUTHORITY_MANIFEST_SHA256 = "6678002a8038ea7cc79ed75d428c669946c67ae66272f1999d4e9d95db8f1595"


def authority_manifest() -> dict[str, object]:
    return {
        "manifest_sha256": SOL_AUTHORITY_MANIFEST_SHA256,
        "source_files": dict(SOL_AUTHORITY_SOURCE_SHA256),
    }


def validate_local_authority(repo_root: str | Path) -> tuple[str, ...]:
    """Verify that the local replay authority is byte-identical to the freeze."""
    root = Path(repo_root)
    encoded = canonical_json(dict(SOL_AUTHORITY_SOURCE_SHA256)).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != SOL_AUTHORITY_MANIFEST_SHA256:
        return ("SOL_AUTHORITY_TABLE_SELF_HASH_MISMATCH",)
    failures: list[str] = []
    for relative, expected in SOL_AUTHORITY_SOURCE_SHA256.items():
        path = root / relative
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            failures.append(f"SOL_AUTHORITY_SOURCE_MISSING:{relative}")
            continue
        if actual != expected:
            failures.append(f"SOL_AUTHORITY_SOURCE_DRIFT:{relative}")
    return tuple(failures)
