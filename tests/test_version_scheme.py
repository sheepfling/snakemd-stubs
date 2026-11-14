"""Regression tests for tag-derived development and release versions."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def _version(repository: Path) -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "setuptools_scm",
            "--root",
            str(repository),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=repository,
    )
    version = json.loads(result.stdout)["version"]
    assert isinstance(version, str)
    return version


def test_tag_and_development_versions_follow_stub_revision_scheme(tmp_path: Path) -> None:
    repository = tmp_path / "version-fixture"
    repository.mkdir()
    project_root = Path(__file__).resolve().parents[1]
    shutil.copyfile(project_root / "pyproject.toml", repository / "pyproject.toml")
    versioned_file = repository / "tracked.txt"
    versioned_file.write_text("release\n")

    subprocess.run(
        ["git", "init", "-b", "master", str(repository)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(repository, "config", "user.name", "Version Scheme Test")
    _git(repository, "config", "user.email", "version-scheme@example.invalid")
    _git(repository, "add", "pyproject.toml", "tracked.txt")
    _git(repository, "commit", "-m", "release")
    _git(repository, "tag", "-a", "v2.4.1.0", "-m", "v2.4.1.0")

    assert _version(repository) == "2.4.1.0"

    versioned_file.write_text("post-release change\n")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "-m", "stub-only fix")

    assert _version(repository) == "2.4.1.1.dev1"
