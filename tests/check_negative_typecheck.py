"""Require the negative consumer fixture to fail at every marked line."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURE = Path(__file__).with_name("negative_typecheck.py.fixture")
DIAGNOSTIC = re.compile(r"negative_typecheck\.py:(\d+)(?::|\s+-\s+error:)")


def main() -> None:
    source = FIXTURE.read_text(encoding="utf-8")
    expected = {
        line_number
        for line_number, line in enumerate(source.splitlines(), start=1)
        if "# expect-error" in line
    }
    if not expected:
        raise SystemExit("negative typing fixture has no expected-error markers")

    with tempfile.TemporaryDirectory(prefix="snakemd-negative-types-") as temporary:
        root = Path(temporary)
        fixture = root / "negative_typecheck.py"
        fixture.write_text(source, encoding="utf-8")
        for tool in ("mypy", "pyright"):
            arguments = [sys.executable, "-m", tool]
            if tool == "pyright":
                arguments.extend(("--pythonpath", sys.executable))
            arguments.append(str(fixture))
            result = subprocess.run(
                arguments,
                cwd=Path.cwd(),
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            observed = {int(match) for match in DIAGNOSTIC.findall(output)}
            if result.returncode == 0 or observed != expected:
                print(output, file=sys.stderr, end="")
                raise SystemExit(
                    f"{tool} expected errors on lines {sorted(expected)}, "
                    f"received exit {result.returncode} and errors on {sorted(observed)}"
                )
            print(f"{tool}: rejected all {len(expected)} marked invalid uses.")


if __name__ == "__main__":
    main()
