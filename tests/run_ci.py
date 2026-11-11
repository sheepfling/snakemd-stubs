"""Run the native CI checks locally or for one hosted matrix target."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_TARGETS = ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15")


@dataclass(frozen=True)
class Target:
    version: str
    interpreter: Path


def _python_in_venv(environment: Path) -> Path:
    executable = "python.exe" if os.name == "nt" else "python"
    scripts = "Scripts" if os.name == "nt" else "bin"
    return environment / scripts / executable


def _python_version(interpreter: Path) -> str:
    result = subprocess.run(
        [
            str(interpreter),
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _resolve_interpreter(value: str) -> Path:
    located = shutil.which(value)
    interpreter = Path(located or value).expanduser().resolve()
    if not interpreter.is_file():
        raise FileNotFoundError(f"Python interpreter does not exist: {interpreter}")
    return interpreter


def _discover_targets() -> list[Target]:
    targets: list[Target] = []
    missing: list[str] = []
    for version in PYTHON_TARGETS:
        located = shutil.which(f"python{version}")
        if located is None:
            missing.append(version)
            continue
        interpreter = Path(located).resolve()
        actual = _python_version(interpreter)
        if actual != version:
            raise RuntimeError(f"python{version} resolved to Python {actual}: {interpreter}")
        targets.append(Target(version, interpreter))
    if missing:
        raise RuntimeError(
            "Missing local Python targets: "
            + ", ".join(missing)
            + ". Install them or run one leg with --target-python."
        )
    return targets


def _run(command: Sequence[str | Path], *, cwd: Path = ROOT) -> None:
    args = [str(item) for item in command]
    print(f"\n$ {shlex.join(args)}", flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def _temporary_workspace() -> tempfile.TemporaryDirectory[str]:
    root = ROOT.resolve()
    parent = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())).resolve()
    if parent == root or parent.is_relative_to(root):
        parent = Path(tempfile.gettempdir()).resolve()
    if parent == root or parent.is_relative_to(root):
        raise RuntimeError(f"Temporary directory must be outside the repository: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="snakemd-ci-", dir=parent)


def _create_environment(base_python: Path, environment: Path, group: str) -> Path:
    _run((base_python, "-m", "venv", environment))
    python = _python_in_venv(environment)
    _run((python, "-m", "pip", "install", "--upgrade", "pip"))
    _run((python, "-m", "pip", "install", "--group", group))
    return python


def _run_repository_quality(checker: Path) -> None:
    print("\n=== Repository quality (Python 3.12 target) ===", flush=True)
    _run((checker, "-m", "ruff", "check", "."))
    _run((checker, "-m", "ruff", "format", "--check", "."))
    _run((checker, "-m", "mypy", "tests/check_typing_fixtures.py"))
    _run((checker.parent / ("mdrepo.exe" if os.name == "nt" else "mdrepo"), "--root", ".", "check"))
    _run(
        (
            checker.parent / ("rumdl.exe" if os.name == "nt" else "rumdl"),
            "--no-config",
            "check",
            "--disable",
            "MD013",
            "--no-cache",
            "--color",
            "never",
            ".",
        )
    )


def _build_distribution(checker: Path, directory: Path) -> Path:
    directory.mkdir()
    _run((checker, "-m", "build", "--outdir", directory))
    _run((checker, "-m", "tests.verify_release_artifacts", directory))
    artifacts = sorted(directory.iterdir())
    if not artifacts:
        raise RuntimeError("Build produced no distribution artifacts")
    _run((checker, "-m", "twine", "check", *artifacts))
    wheels = [artifact for artifact in artifacts if artifact.suffix == ".whl"]
    if len(wheels) != 1:
        raise RuntimeError(f"Expected one wheel, found {len(wheels)}")
    return wheels[0]


def _run_target(checker: Path, target: Target, workspace: Path) -> None:
    print(f"\n=== Python {target.version} ===", flush=True)
    target_root = workspace / f"target-{target.version}"
    target_python = _create_environment(target.interpreter, target_root, "target")

    if target.version == "3.12":
        _run_repository_quality(checker)

    wheel = _build_distribution(checker, workspace / f"dist-{target.version}")
    _run((target_python, "-m", "pip", "install", "--no-deps", "--force-reinstall", wheel))

    consumer = workspace / f"consumer-{target.version}"
    consumer.mkdir()
    origin_check = (
        "from importlib.metadata import distribution; "
        "from pathlib import Path; "
        "installed = Path(distribution('snakemd-stubs').locate_file('snakemd-stubs')).resolve(); "
        "assert not installed.is_relative_to(Path.cwd().resolve()), installed; "
        "print(installed)"
    )
    _run((target_python, "-c", origin_check), cwd=consumer)
    _run(
        (
            checker,
            "-m",
            "tests.check_typing_fixtures",
            "--target-python",
            target_python,
            "--require-checker",
            "mypy",
            "--require-checker",
            "pyright",
            "--require-checker",
            "ty",
        )
    )
    _run((target_python, "-m", "pytest", "-q"))
    _run(
        (
            target_python,
            "-m",
            "mypy.stubtest",
            "--allowlist",
            ROOT / "stubtest-allowlist.txt",
            "snakemd",
        ),
        cwd=consumer,
    )
    _run((target_python, "-m", "tests.runtime_smoke"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-python",
        help=(
            "run one matrix leg with this base interpreter; without it, discover and run "
            "Python 3.10–3.15"
        ),
    )
    args = parser.parse_args()

    checker_version = _python_version(Path(sys.executable).resolve())
    if checker_version != "3.12":
        parser.error(f"Run the CI runner with Python 3.12 (got {checker_version})")
    try:
        if args.target_python:
            interpreter = _resolve_interpreter(args.target_python)
            version = _python_version(interpreter)
            if version not in PYTHON_TARGETS:
                parser.error(
                    f"Unsupported target Python {version}; expected one of "
                    f"{', '.join(PYTHON_TARGETS)}"
                )
            targets = [Target(version, interpreter)]
        else:
            targets = _discover_targets()
            targets.sort(key=lambda target: target.version != "3.12")
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exception:
        parser.error(str(exception))

    print("Running target(s): " + ", ".join(target.version for target in targets))

    failures: list[tuple[str, str]] = []
    with _temporary_workspace() as directory:
        workspace = Path(directory)
        checker = _create_environment(Path(sys.executable).resolve(), workspace / "checker", "dev")
        for target in targets:
            try:
                _run_target(checker, target, workspace)
            except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
                failures.append((target.version, str(error)))
                print(f"\nFAILED Python {target.version}: {error}", file=sys.stderr, flush=True)

    if failures:
        print("\nLocal CI failed:", file=sys.stderr)
        for version, message in failures:
            print(f"  Python {version}: {message}", file=sys.stderr)
        return 1
    print("\nLocal CI passed for: " + ", ".join(target.version for target in targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
