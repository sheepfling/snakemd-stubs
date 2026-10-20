"""Build externally and verify the installed wheel from a clean consumer dir."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_FILES = ("pyproject.toml", "requirements-compat.txt", "stubtest-allowlist.txt")
IGNORED_BUILD_PATHS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".rumdl_cache",
    "build",
    "dist",
    "__pycache__",
    "venv",
    ".venv",
}


def copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name in IGNORED_BUILD_PATHS}
    ignored.update(name for name in names if name.endswith(".egg-info") or name.endswith(".pyc"))
    return ignored


def run_step(name: str, arguments: list[str], cwd: Path) -> float:
    print(f"==> {name}", flush=True)
    started = time.monotonic()
    result = subprocess.run(arguments, cwd=cwd, check=False)
    elapsed = time.monotonic() - started
    print(f"{name}: exit={result.returncode}, elapsed={elapsed:.2f}s", flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    return elapsed


def prepare_source_copy(destination: Path) -> None:
    shutil.copytree(ROOT, destination, ignore=copy_ignore)


def prepare_consumer(source_copy: Path, destination: Path) -> None:
    destination.mkdir()
    for relative in CONSUMER_FILES:
        source = source_copy / relative
        shutil.copy2(source, destination / relative)
    shutil.copytree(source_copy / "tests", destination / "tests")


def built_distributions(directory: Path) -> tuple[Path, Path]:
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit(
            f"Expected one wheel and one sdist in {directory}; "
            f"found {len(wheels)} wheel(s) and {len(sdists)} sdist(s)"
        )
    return wheels[0], sdists[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-twine",
        action="store_true",
        help="also run Twine metadata validation (included in the full local profile)",
    )
    options = parser.parse_args()

    elapsed = 0.0
    with tempfile.TemporaryDirectory(prefix="snakemd-coverage-") as temporary:
        temp_root = Path(temporary)
        source_copy = temp_root / "source"
        dist_dir = temp_root / "dist"
        consumer = temp_root / "consumer"
        dist_dir.mkdir()

        prepare_source_copy(source_copy)
        prepare_consumer(source_copy, consumer)

        elapsed += run_step(
            "Build wheel and sdist outside the checkout",
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                str(dist_dir),
                str(source_copy),
            ],
            cwd=temp_root,
        )
        wheel, sdist = built_distributions(dist_dir)

        if options.with_twine:
            elapsed += run_step(
                "Twine artifact metadata",
                [sys.executable, "-m", "twine", "check", str(wheel), str(sdist)],
                cwd=temp_root,
            )

        elapsed += run_step(
            "Install built wheel into the active verification environment",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ],
            cwd=temp_root,
        )
        elapsed += run_step(
            "Installed dependency consistency",
            [sys.executable, "-m", "pip", "check"],
            cwd=consumer,
        )
        elapsed += run_step(
            "Runtime-to-stub API inventory",
            [sys.executable, "-m", "tests.audit_api_coverage"],
            cwd=consumer,
        )
        elapsed += run_step(
            "Positive mypy consumer probe",
            [sys.executable, "-m", "mypy", "tests/typecheck.py"],
            cwd=consumer,
        )
        elapsed += run_step(
            "Positive Pyright consumer probe",
            [
                sys.executable,
                "-m",
                "pyright",
                "--pythonpath",
                sys.executable,
                "tests/typecheck.py",
            ],
            cwd=consumer,
        )
        elapsed += run_step(
            "Expected-negative mypy and Pyright probes",
            [sys.executable, "-m", "tests.check_negative_typecheck"],
            cwd=consumer,
        )
        elapsed += run_step(
            "Stubtest runtime compatibility",
            [
                sys.executable,
                "-m",
                "mypy.stubtest",
                "--allowlist",
                "stubtest-allowlist.txt",
                "snakemd",
            ],
            cwd=consumer,
        )
        elapsed += run_step(
            "Runtime consumer smoke",
            [sys.executable, "-m", "tests.runtime_smoke"],
            cwd=consumer,
        )

    print(f"Compatibility aggregate passed in {elapsed:.2f}s of measured tool time.")


if __name__ == "__main__":
    main()
