"""Release-critical packaging metadata checks.

These checks exercise installed distribution metadata.  They complement the
clean-environment replay documented in engineering/release_v0_1/INSTALLATION.md.
"""

from importlib import metadata

from packaging.requirements import Requirement
import symbolic_compactification
import yaml


DIST_NAME = "symbolic-compactification"


def test_distribution_and_runtime_versions_are_consistent() -> None:
    assert metadata.version(DIST_NAME) == symbolic_compactification.__version__
    assert yaml.__version__


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
