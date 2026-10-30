"""Validation tests for the native typing-fixture configuration."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import pytest

from tests import check_typing_fixtures
from tests.check_typing_fixtures import (
    FixtureConfig,
    _command,
    _diagnostic_lines,
    _parse_config,
)


def _document() -> dict[str, object]:
    return {
        "verification": {
            "positive_fixture": "tests/typecheck.py",
            "negative_fixture": "tests/negative_typecheck.py.fixture",
            "typing_checkers": ["mypy", "pyright", "ty"],
            "ty_diagnostics": ["Expected `str`, found `Literal[42]`"],
        }
    }


def test_parse_config_returns_validated_fixture_config() -> None:
    config = _parse_config(_document())

    assert isinstance(config, FixtureConfig)
    assert config.positive_fixture == Path("tests/typecheck.py")
    assert config.negative_fixture == Path("tests/negative_typecheck.py.fixture")
    assert config.typing_checkers == ("mypy", "pyright", "ty")
    assert config.ty_diagnostics == ("Expected `str`, found `Literal[42]`",)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("positive_fixture", "", "non-empty relative path"),
        ("negative_fixture", "/tmp/negative.py", "stay inside the repository"),
        ("negative_fixture", "../negative.py", "stay inside the repository"),
        ("typing_checkers", ["mypy", "mypy"], "once each"),
        ("typing_checkers", ["other"], "mypy, pyright, and/or ty"),
        ("negative_expected_count", True, "positive integer"),
        ("mypy_diagnostics", [1], "list of strings"),
        ("ty_diagnostics", [1], "list of strings"),
    ],
)
def test_parse_config_rejects_invalid_values(field: str, value: object, message: str) -> None:
    document = _document()
    verification = cast(dict[str, object], document["verification"])
    verification[field] = value

    with pytest.raises(ValueError, match=message):
        _parse_config(document)


def test_ty_command_uses_installed_target_python_and_project_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def find_checker(name: str, path: str) -> str:
        assert name == "ty"
        assert Path(path) == Path(sys.executable).parent
        return str(Path(path) / "ty")

    monkeypatch.setattr(check_typing_fixtures.shutil, "which", find_checker)
    command = _command(
        "ty",
        Path("tests/typecheck.py"),
        Path("/repo/pyproject.toml"),
        Path("/target/python"),
        "3.15",
    )

    assert command[0] == str(Path(sys.executable).parent / "ty")
    assert Path(command[0]).name.startswith("ty")
    assert command[1:3] == ["check", "--project"]
    assert command[3] == "/repo"
    assert command[command.index("--python") + 1] == "/target/python"
    assert command[command.index("--python-version") + 1] == "3.15"
    assert command[-1] == "tests/typecheck.py"


def test_ty_diagnostic_lines_capture_rule_errors_only() -> None:
    output = (
        "tests/negative_typecheck.py.fixture:6:15: "
        "error[invalid-argument-type] Argument is incorrect\n"
        "Found 1 diagnostic"
    )

    assert _diagnostic_lines("ty", output, "negative_typecheck.py.fixture") == {
        6: [output.splitlines()[0]]
    }
