"""Validation tests for the native typing-fixture configuration."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from tests.check_typing_fixtures import FixtureConfig, _parse_config


def _document() -> dict[str, object]:
    return {
        "verification": {
            "positive_fixture": "tests/typecheck.py",
            "negative_fixture": "tests/negative_typecheck.py.fixture",
            "typing_checkers": ["mypy", "pyright"],
        }
    }


def test_parse_config_returns_validated_fixture_config() -> None:
    config = _parse_config(_document())

    assert isinstance(config, FixtureConfig)
    assert config.positive_fixture == Path("tests/typecheck.py")
    assert config.negative_fixture == Path("tests/negative_typecheck.py.fixture")
    assert config.typing_checkers == ("mypy", "pyright")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("positive_fixture", "", "non-empty relative path"),
        ("negative_fixture", "/tmp/negative.py", "stay inside the repository"),
        ("negative_fixture", "../negative.py", "stay inside the repository"),
        ("typing_checkers", ["mypy", "mypy"], "once each"),
        ("typing_checkers", ["other"], "mypy and/or pyright"),
        ("negative_expected_count", True, "positive integer"),
        ("mypy_diagnostics", [1], "list of strings"),
    ],
)
def test_parse_config_rejects_invalid_values(field: str, value: object, message: str) -> None:
    document = _document()
    verification = cast(dict[str, object], document["verification"])
    verification[field] = value

    with pytest.raises(ValueError, match=message):
        _parse_config(document)
