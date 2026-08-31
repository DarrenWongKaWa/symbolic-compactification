#!/bin/sh
# Offline replay of bundled derivation-audit expressions and manifests.
# Does not use the network.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPLAY="$ROOT/replay"

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

ssc_audit verify "$REPLAY"
ssc_audit table "$REPLAY"
