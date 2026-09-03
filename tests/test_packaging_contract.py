"""Release-critical packaging metadata checks.

These checks exercise installed distribution metadata.
"""

from importlib import metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10; tomllib is 3.11+
    import tomli as tomllib

from packaging.requirements import Requirement
from packaging.version import Version
import pytest
import symbolic_compactification
import yaml

from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PACKAGE_VERSION,
    RELEASE_VERSION,
)


DIST_NAME = "symbolic-compactification"
pytestmark = pytest.mark.release_critical


def test_distribution_and_runtime_versions_are_consistent() -> None:
    assert metadata.version(DIST_NAME) == symbolic_compactification.__version__
    assert yaml.__version__


def test_alpha_release_identity_is_explicit_and_pep440_aligned() -> None:
    project = tomllib.loads(
        Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["version"] == RELEASE_VERSION == "0.3.2-alpha"
    assert Version(RELEASE_VERSION) == Version(PACKAGE_VERSION)
    assert metadata.version(DIST_NAME) == PACKAGE_VERSION == "0.3.2a0"
    assert ENGINE_VERSION == AGENT_PROTOCOL_VERSION == "0.3.0"
    assert project["description"] == (
        "Agent-assisted scientific derivation-audit with reviewer HTML."
    )


def test_workspace_yaml_dependency_is_declared_and_bounded() -> None:
    requirements = [Requirement(item) for item in metadata.requires(DIST_NAME) or []]
    pyyaml = next(
        requirement
        for requirement in requirements
        if requirement.name.lower() == "pyyaml" and requirement.marker is None
    )
    assert pyyaml.specifier.contains("6.0")
    assert not pyyaml.specifier.contains("7.0")


def test_both_supported_console_entry_points_are_packaged() -> None:
    entry_points = {
        entry_point.name: entry_point.value
        for entry_point in metadata.entry_points(group="console_scripts")
    }
    target = "symbolic_compactification.cli:main"
    assert entry_points["symbolic-compactification"] == target
    assert entry_points["ssc"] == target


def _checkout_identity(repository: Path) -> str:
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    return f"{commit}{'-dirty' if status.strip() else ''}"


@pytest.mark.parametrize("install_kind", ["source", "wheel"])
def test_non_editable_install_records_build_revision_outside_checkout(
        tmp_path, install_kind) -> None:
    """Exercise both PEP 517 install paths without importing checkout code."""
    repository = Path(__file__).resolve().parents[1]
    expected = _checkout_identity(repository)
    install_root = tmp_path / f"installed-{install_kind}"
    outside = tmp_path / f"outside-{install_kind}"
    outside.mkdir()
    source: Path = repository

    environment = os.environ.copy()
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment.pop("PYTHONPATH", None)
    if install_kind == "wheel":
        wheel_directory = tmp_path / "wheelhouse"
        wheel_directory.mkdir()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-cache-dir",
                "--no-deps",
                "--wheel-dir",
                str(wheel_directory),
                str(repository),
            ],
            cwd=outside,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        source = next(wheel_directory.glob("*.whl"))

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--no-deps",
            "--target",
            str(install_root),
            str(source),
        ],
        cwd=outside,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    # ``--target`` intentionally reuses the test interpreter's dependencies,
    # while PYTHONPATH forces the non-editable built package to be imported.
    runtime_environment = environment.copy()
    runtime_environment["PYTHONPATH"] = str(install_root)
    workspace = outside / "workspace"
    init = subprocess.run(
        [
            sys.executable,
            "-m",
            "symbolic_compactification.cli",
            "init",
            str(workspace),
            "--json",
        ],
        cwd=outside,
        env=runtime_environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(init.stdout)["status"] == "WORKSPACE_INITIALIZED"
    verified = subprocess.run(
        [
            sys.executable,
            "-m",
            "symbolic_compactification.cli",
            "verify",
            str(workspace),
            "--json",
        ],
        cwd=outside,
        env=runtime_environment,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(verified.stdout)
    provenance = json.loads(
        Path(payload["provenance_path"]).read_text(encoding="utf-8")
    )

    assert payload["result"] == "ZERO"
    assert provenance["git_commit"] == expected
    assert re.fullmatch(r"[0-9a-f]{40}(?:-dirty)?", expected)


def test_packaged_readme_is_the_research_preview_entrypoint() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "derivation-audit" in readme.lower() or "derivation audit" in readme.lower()
    assert "Forward derivation" in readme
    assert all(verdict in readme for verdict in ("ZERO", "NONZERO", "UNKNOWN"))
    assert "examples/guo-evidence-ledger" in readme
    assert "Publication decision: **E**" not in readme
    assert "AI discovers physics" not in readme
