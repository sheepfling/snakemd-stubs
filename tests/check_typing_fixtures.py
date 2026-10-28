"""Run positive and expected-negative fixtures with native Mypy and Pyright."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


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
    else:
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
    command.append(str(fixture))
    return command


def _diagnostic_lines(checker: str, output: str, fixture_name: str) -> dict[int, list[str]]:
    pattern = r"^.*?:(\d+): error:" if checker == "mypy" else r"^.*?:(\d+):\d+ - error:"
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
    root: Path, negative: Path, config: dict[str, Any], checker: str
) -> tuple[set[int] | None, int | None, list[str]]:
    lines = {
        number
        for number, line in enumerate(negative.read_text(encoding="utf-8").splitlines(), start=1)
        if "# expect-error" in line
    }
    if lines:
        return lines, None, []
    verification = config.get("verification", {})
    expected_count = verification.get("negative_expected_count")
    if not isinstance(expected_count, int) or expected_count < 1:
        raise ValueError(
            "negative fixture must use # expect-error markers or set negative_expected_count"
        )
    diagnostics = verification.get(f"{checker}_diagnostics", [])
    if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
        raise ValueError(f"{checker}_diagnostics must be a list of strings")
    return None, expected_count, diagnostics


def _check(root: Path, config: dict[str, Any], checker: str, target: Path, version: str) -> bool:
    verification = config.get("verification", {})
    positive = (root / verification["positive_fixture"]).resolve()
    negative = (root / verification["negative_fixture"]).resolve()
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

    expected_lines, expected_count, expected_messages = _expected_errors(
        root, negative, config, checker
    )
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
        config = json.loads(config_path.read_text(encoding="utf-8"))
        version = _target_version(target)
        checkers = config["verification"].get("typing_checkers", ["mypy", "pyright"])
        if (
            not isinstance(checkers, list)
            or not checkers
            or any(checker not in {"mypy", "pyright"} for checker in checkers)
        ):
            raise ValueError("typing_checkers must contain mypy and/or pyright")
        for checker in checkers:
            if not _check(root, config, checker, target, version):
                return 1
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
