"""Thin local/CI entry point for the pinned Alphus stub-package gates."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("quality", help="Run the repository's native quality profile")
    target = commands.add_parser("target", help="Verify a wheel in the target venv")
    target.add_argument("--target-python", required=True)
    target.add_argument("--report", default=None)
    args = parser.parse_args(argv)
    if args.command == "quality":
        steps = [
            [
                sys.executable,
                "-m",
                "alphus",
                "--root",
                str(ROOT),
                "--config",
                "quality-gates.toml",
                "--profile",
                "quality",
                "--run",
            ]
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "alphus.gates.stubs.verify",
            "--root",
            str(ROOT),
            "--config",
            "stub-quality.json",
            "--with-twine",
            "--target-python",
            args.target_python,
        ]
        if args.report:
            command.extend(["--report", args.report])
        steps = [command, [args.target_python, "-m", "pytest", "-q"]]
    for command in steps:
        environment = os.environ.copy()
        scripts = str(Path(command[0]).absolute().parent)
        environment["PATH"] = os.pathsep.join(
            part for part in (scripts, environment.get("PATH", "")) if part
        )
        try:
            result = subprocess.run(command, cwd=ROOT, check=False, env=environment)
        except OSError as error:
            print(f"Unable to start CI command: {error}", file=sys.stderr)
            return 127
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
