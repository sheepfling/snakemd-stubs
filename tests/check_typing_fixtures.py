"""Run positive and expected-negative fixtures with native Mypy, Pyright, and ty."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_CHECKERS = frozenset({"mypy", "pyright", "ty"})


@dataclass(frozen=True)
class FixtureConfig:
    positive_fixture: Path
    negative_fixture: Path
    typing_checkers: tuple[str, ...]
    negative_expected_count: int | None
    mypy_diagnostics: tuple[str, ...]
    pyright_diagnostics: tuple[str, ...]
    ty_diagnostics: tuple[str, ...]


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be an object with string keys")
    return cast(dict[str, object], value)


def _fixture_path(verification: dict[str, object], field: str) -> Path:
    value = verification.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"verification.{field} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"verification.{field} must stay inside the repository")
    return path


def _diagnostic_messages(verification: dict[str, object], checker: str) -> tuple[str, ...]:
    value = verification.get(f"{checker}_diagnostics", [])
    if not isinstance(value, list) or any(
        not isinstance(message, str) or not message.strip() for message in value
    ):
        raise ValueError(f"verification.{checker}_diagnostics must be a list of strings")
    return tuple(cast(list[str], value))


def _parse_config(document: object) -> FixtureConfig:
    root = _mapping(document, "stub-quality.json")
    verification = _mapping(root.get("verification"), "verification")
    checkers = verification.get("typing_checkers", ["mypy", "pyright", "ty"])
    if (
        not isinstance(checkers, list)
        or not checkers
        or any(
            not isinstance(checker, str) or checker not in SUPPORTED_CHECKERS
            for checker in checkers
        )
        or len(set(checkers)) != len(checkers)
    ):
        raise ValueError(
            "verification.typing_checkers must list mypy, pyright, and/or ty once each"
        )
    expected_count = verification.get("negative_expected_count")
    if expected_count is not None and (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count < 1
    ):
        raise ValueError("verification.negative_expected_count must be a positive integer")
    return FixtureConfig(
        positive_fixture=_fixture_path(verification, "positive_fixture"),
        negative_fixture=_fixture_path(verification, "negative_fixture"),
        typing_checkers=tuple(cast(list[str], checkers)),
        negative_expected_count=expected_count,
        mypy_diagnostics=_diagnostic_messages(verification, "mypy"),
        pyright_diagnostics=_diagnostic_messages(verification, "pyright"),
        ty_diagnostics=_diagnostic_messages(verification, "ty"),
    )


def _target_version(target_python: Path) -> str:
    output = subprocess.run(
        [
            str(target_python),
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return output.strip()


def _command(
    checker: str, fixture: Path, config: Path, target_python: Path, version: str
) -> list[str]:
    command = [sys.executable, "-m", checker]
    if checker == "mypy":
        command.extend(
            (
                "--config-file",
                str(config),
                "--python-executable",
                str(target_python),
                "--python-version",
                version,
                "--no-incremental",
            )
        )
    elif checker == "pyright":
        command.extend(
            (
                "--project",
                str(config),
                "--pythonpath",
                str(target_python),
                "--pythonversion",
                version,
            )
        )
    else:
        checker_environment = Path(sys.executable).parent
        ty_executable = shutil.which("ty", path=str(checker_environment))
        if ty_executable is None:
            raise FileNotFoundError(
                f"ty CLI is not installed in checker environment {checker_environment}"
            )
        command = [
            ty_executable,
            "check",
            "--project",
            str(config.parent),
            "--python",
            str(target_python),
            "--python-version",
            version,
            "--output-format",
            "concise",
            "--color",
            "never",
            "--no-progress",
        ]
    command.append(str(fixture))
    return command


def _diagnostic_lines(checker: str, output: str, fixture_name: str) -> dict[int, list[str]]:
    if checker == "mypy":
        pattern = r"^.*?:(\d+): error:"
    elif checker == "pyright":
        pattern = r"^.*?:(\d+):\d+ - error:"
    else:
        pattern = r"^.*?:(\d+):\d+:\s+error(?:\[[^]]+\])?"
    diagnostics: dict[int, list[str]] = {}
    for line in output.splitlines():
        match = re.search(pattern, line)
        if fixture_name in line and match is not None:
            diagnostics.setdefault(int(match.group(1)), []).append(line)
    return diagnostics


def _run(checker: str, fixture: Path, config: Path, target: Path, version: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="stub-fixture-check-") as directory:
        result = subprocess.run(
            _command(checker, fixture, config, target, version),
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
    return result.returncode, result.stdout + result.stderr


def _expected_errors(
    negative: Path, config: FixtureConfig, checker: str
) -> tuple[set[int] | None, int | None, list[str]]:
    lines = {
        number
        for number, line in enumerate(negative.read_text(encoding="utf-8").splitlines(), start=1)
        if "# expect-error" in line
    }
    if lines:
        return lines, None, []
    if config.negative_expected_count is None:
        raise ValueError(
            "negative fixture must use # expect-error markers or set negative_expected_count"
        )
    diagnostics = getattr(config, f"{checker}_diagnostics")
    return None, config.negative_expected_count, list(diagnostics)


def _check(root: Path, config: FixtureConfig, checker: str, target: Path, version: str) -> bool:
    repository = root.resolve()
    positive = (repository / config.positive_fixture).resolve()
    negative = (repository / config.negative_fixture).resolve()
    if not positive.is_relative_to(repository) or not negative.is_relative_to(repository):
        raise ValueError("configured typing fixtures must stay inside the repository")
    if not positive.is_file() or not negative.is_file():
        raise ValueError("configured positive or negative typing fixture is missing")

    positive_status, positive_output = _run(
        checker, positive, root / "pyproject.toml", target, version
    )
    positive_errors = _diagnostic_lines(checker, positive_output, positive.name)
    if positive_status != 0 or positive_errors:
        print(f"FAIL {checker} positive fixture:\n{positive_output}", file=sys.stderr)
        return False
    print(f"PASS {checker} positive fixture for Python {version}")

    expected_lines, expected_count, expected_messages = _expected_errors(negative, config, checker)
    negative_status, negative_output = _run(
        checker, negative, root / "pyproject.toml", target, version
    )
    actual = _diagnostic_lines(checker, negative_output, negative.name)
    if negative_status == 0:
        print(f"FAIL {checker} accepted the negative fixture:\\n{negative_output}", file=sys.stderr)
        return False
    if expected_lines is not None:
        if set(actual) != expected_lines:
            found = {line: len(items) for line, items in actual.items()}
            print(
                f"FAIL {checker} negative fixture: expected errors on marked lines "
                f"{sorted(expected_lines)}, found {found}\n"
                f"{negative_output}",
                file=sys.stderr,
            )
            return False
    elif sum(map(len, actual.values())) != expected_count:
        print(
            f"FAIL {checker} negative fixture: expected {expected_count} errors, "
            f"found {sum(map(len, actual.values()))}\n{negative_output}",
            file=sys.stderr,
        )
        return False
    missing = [
        message
        for message in expected_messages
        if message.casefold() not in negative_output.casefold()
    ]
    if missing:
        print(
            f"FAIL {checker} negative fixture missing expected diagnostics {missing}:\n"
            f"{negative_output}",
            file=sys.stderr,
        )
        return False
    count = len(expected_lines) if expected_lines is not None else expected_count
    print(f"PASS {checker} rejected {count} expected invalid calls for Python {version}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target-python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    target = args.target_python.expanduser().absolute()
    config_path = root / "stub-quality.json"
    try:
        config = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
        version = _target_version(target)
        for checker in config.typing_checkers:
            if not _check(root, config, checker, target, version):
                return 1
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
