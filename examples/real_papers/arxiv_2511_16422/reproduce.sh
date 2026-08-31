#!/bin/sh
# Offline replay of the public arXiv:2511.16422v2 derivation-audit workspace.
# Does not fetch the network. Requires a local install of
# symbolic-compactification 0.2.0-alpha.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

ssc_audit() {
  if command -v symbolic-compactification >/dev/null 2>&1; then
    symbolic-compactification audit "$@"
  elif command -v ssc >/dev/null 2>&1; then
    ssc audit "$@"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m symbolic_compactification.cli audit "$@"
  elif command -v python >/dev/null 2>&1; then
    python -m symbolic_compactification.cli audit "$@"
  else
    die "symbolic-compactification is not installed (offline replay requires a local install)"
  fi
}

ssc_audit inventory "$ROOT"
ssc_audit inspect "$ROOT"
ssc_audit verify "$ROOT"
ssc_audit table "$ROOT"
ssc_audit report "$ROOT"
ssc_audit package "$ROOT"

# Overlay cannot create ZERO; it only annotates machine TABLE_VERIFIED rows.
if command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/annotate_strength.py"
elif command -v python >/dev/null 2>&1; then
  python "$ROOT/annotate_strength.py"
else
  die "python3 is required to annotate verification strength"
fi
