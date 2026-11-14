"""Tests for the release artifact version guard."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from tests.verify_release_artifacts import main, verify_artifacts


def _write_artifacts(
    dist_dir: Path,
    version: str = "2.4.1.0",
    sdist_version: str | None = None,
    nested_sdist_version: str | None = None,
) -> None:
    dist_dir.mkdir()
    metadata = f"Metadata-Version: 2.4\nName: snakemd-stubs\nVersion: {version}\n\n"
    wheel = dist_dir / f"snakemd_stubs-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(f"snakemd_stubs-{version}.dist-info/METADATA", metadata)

    source_version = sdist_version or version
    sdist_metadata = f"Metadata-Version: 2.4\nName: snakemd-stubs\nVersion: {source_version}\n\n"
    sdist = dist_dir / f"snakemd_stubs-{source_version}.tar.gz"
    member_name = f"snakemd_stubs-{source_version}/PKG-INFO"
    with tarfile.open(sdist, "w:gz") as archive:
        contents = sdist_metadata.encode("utf-8")
        member = tarfile.TarInfo(member_name)
        member.size = len(contents)
        archive.addfile(member, io.BytesIO(contents))
        if nested_sdist_version is not None:
            nested_metadata = (
                f"Metadata-Version: 2.4\nName: snakemd-stubs\nVersion: {nested_sdist_version}\n\n"
            )
            nested_contents = nested_metadata.encode("utf-8")
            nested_member = tarfile.TarInfo(
                f"snakemd_stubs-{source_version}/snakemd_stubs.egg-info/PKG-INFO"
            )
            nested_member.size = len(nested_contents)
            archive.addfile(nested_member, io.BytesIO(nested_contents))


def test_verify_artifacts_matches_release_tag(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir)

    assert verify_artifacts(dist_dir, "v2.4.1.0") == "2.4.1.0"


def test_verify_artifacts_accepts_development_version_without_tag(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir, "2.4.1.1.dev23")

    assert verify_artifacts(dist_dir) == "2.4.1.1.dev23"


def test_verify_artifacts_accepts_matching_nested_sdist_metadata(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir, nested_sdist_version="2.4.1.0")

    assert verify_artifacts(dist_dir) == "2.4.1.0"


@pytest.mark.parametrize("tag", ["2.4.1.0", "v2.4.1", "v2.4.1.0rc1", "v02.4.1.0"])
def test_verify_artifacts_rejects_noncanonical_release_tag(tmp_path: Path, tag: str) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir)

    with pytest.raises(ValueError, match="invalid release tag"):
        verify_artifacts(dist_dir, tag)


def test_verify_artifacts_rejects_tag_mismatch(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir)

    with pytest.raises(ValueError, match="does not match release tag"):
        verify_artifacts(dist_dir, "v2.4.1.1")


def test_verify_artifacts_rejects_wheel_sdist_mismatch(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir, sdist_version="2.4.1.1")

    with pytest.raises(ValueError, match="wheel version 2.4.1.0 does not match sdist"):
        verify_artifacts(dist_dir)


def test_verify_artifacts_rejects_disagreeing_nested_sdist_metadata(
    tmp_path: Path,
) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir, nested_sdist_version="2.4.1.1")

    with pytest.raises(ValueError, match="source metadata versions disagree"):
        verify_artifacts(dist_dir)


def test_cli_reports_verified_release_version(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    _write_artifacts(dist_dir)
    stdout = io.StringIO()

    assert main(["--tag", "v2.4.1.0", str(dist_dir)], stdout) == 0
    assert stdout.getvalue() == "Verified snakemd-stubs 2.4.1.0 wheel and sdist\n"
