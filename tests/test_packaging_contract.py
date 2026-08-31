"""Release-critical packaging metadata checks.

These checks exercise installed distribution metadata.  They complement the
clean-environment replay documented in engineering/release_v0_1/INSTALLATION.md.
"""

from importlib import metadata
from pathlib import Path
import tomllib

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

    assert project["version"] == RELEASE_VERSION == "0.1.0-alpha"
    assert Version(RELEASE_VERSION) == Version(PACKAGE_VERSION)
    assert metadata.version(DIST_NAME) == PACKAGE_VERSION == "0.1.0a0"
    assert ENGINE_VERSION == AGENT_PROTOCOL_VERSION == "0.3.0"
    assert project["description"] == (
        "Context-grounded symbolic hypotheses with fail-closed verification."
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
