"""Fail when tracked runtime/scientific input artifacts cross the firewall."""
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root,
        capture_output=True, check=True)
    tracked = [Path(item.decode("utf-8"))
               for item in result.stdout.split(b"\0") if item]

    offenders = []
    for path in tracked:
        parts = path.parts
        if parts and parts[0] == "reference":
            offenders.append(path)
        if len(parts) >= 2 and parts[:2] == ("workspace", "runs") \
                and path.name != ".gitkeep":
            offenders.append(path)
        if len(parts) >= 2 and parts[:2] == ("workspace", "input") \
                and path.name != ".gitkeep":
            offenders.append(path)

    if offenders:
        for path in sorted(set(offenders), key=str):
            print(f"tracked clean-room violation: {path}")
        return 1
    print("tracked scientific/runtime contamination artifacts: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
