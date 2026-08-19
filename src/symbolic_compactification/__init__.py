"""Standalone symbolic compactification engine.

Kernel modules:
  models    - shared data types, verdict constants, symbol normalization
  parser    - strict whitelist SymPy parser (fail-closed, no eval/exec)
  verifier  - exact residual verification (ZERO / NONZERO / UNKNOWN)
  residual  - residual construction and session recording helpers

Session persistence and the CLI are owned by later layers and are
intentionally not part of this kernel.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
