"""Check that built distributions match this project's version and release tag."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path, PurePosixPath
from typing import TextIO

PROJECT_NAME = "snakemd-stubs"
PROJECT_NAME_NORMALIZED = "snakemd-stubs"
VERSION_PATTERN = r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){3}"
PACKAGE_VERSION_RE = re.compile(rf"{VERSION_PATTERN}(?:\.dev(?:0|[1-9][0-9]*))?\Z")
RELEASE_TAG_RE = re.compile(rf"v(?P<version>{VERSION_PATTERN})\Z")


def _normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _version_from_tag(tag: str) -> str:
    match = RELEASE_TAG_RE.fullmatch(tag)
    if match is None:
        raise ValueError(f"invalid release tag {tag!r}; expected vMAJOR.MINOR.PATCH.STUB_REV")
    return match.group("version")


def _metadata_version(metadata: str, artifact: Path) -> str:
    message = Parser().parsestr(metadata)
    name = message.get("Name", "")
    if _normalize_name(name) != PROJECT_NAME_NORMALIZED:
        raise ValueError(f"{artifact.name} metadata names {name!r}, expected {PROJECT_NAME}")
    version = message.get("Version")
    if version is None or PACKAGE_VERSION_RE.fullmatch(version) is None:
        raise ValueError(f"{artifact.name} has invalid four-part package version {version!r}")
    return version


def _wheel_version(artifact: Path) -> str:
    try:
        with zipfile.ZipFile(artifact) as archive:
            metadata_names = [
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_names) != 1:
                raise ValueError(
                    f"{artifact.name} must contain one .dist-info/METADATA file; "
                    f"found {len(metadata_names)}"
                )
            metadata = archive.read(metadata_names[0]).decode("utf-8")
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read wheel metadata from {artifact.name}: {error}") from error
    return _metadata_version(metadata, artifact)


def _sdist_version(artifact: Path) -> str:
    try:
        with tarfile.open(artifact, "r:gz") as archive:
            metadata_members = [
                member
                for member in archive.getmembers()
                if member.isfile() and PurePosixPath(member.name).name == "PKG-INFO"
            ]
            top_level_metadata = [
                member for member in metadata_members if len(PurePosixPath(member.name).parts) == 2
            ]
            if len(top_level_metadata) != 1:
                raise ValueError(
                    f"{artifact.name} must contain one top-level PKG-INFO file; "
                    f"found {len(top_level_metadata)}"
                )
            versions: list[str] = []
            for member in metadata_members:
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"cannot read {member.name} from {artifact.name}")
                metadata = stream.read().decode("utf-8")
                versions.append(_metadata_version(metadata, artifact))
    except (OSError, tarfile.TarError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read source metadata from {artifact.name}: {error}") from error
    if len(set(versions)) != 1:
        raise ValueError(f"source metadata versions disagree inside {artifact.name}: {versions}")
    return versions[0]


def verify_artifacts(dist_dir: Path, tag: str | None = None) -> str:
    """Verify one wheel and one sdist, returning their shared package version."""
    expected_version = _version_from_tag(tag) if tag is not None else None
    if not dist_dir.is_dir():
        raise ValueError(f"distribution directory does not exist: {dist_dir}")

    artifacts = sorted(dist_dir.iterdir())
    wheels = [path for path in artifacts if path.is_file() and path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.is_file() and path.name.endswith(".tar.gz")]
    if len(artifacts) != 2 or len(wheels) != 1 or len(sdists) != 1:
        raise ValueError(
            "expected exactly one wheel and one .tar.gz sdist in "
            f"{dist_dir}; found {[path.name for path in artifacts]}"
        )

    wheel, sdist = wheels[0], sdists[0]
    wheel_version = _wheel_version(wheel)
    sdist_version = _sdist_version(sdist)
    if wheel_version != sdist_version:
        raise ValueError(
            f"wheel version {wheel_version} does not match sdist version {sdist_version}"
        )
    if expected_version is not None and wheel_version != expected_version:
        raise ValueError(
            f"artifact version {wheel_version} does not match release tag version "
            f"{expected_version}"
        )
    expected_wheel = f"snakemd_stubs-{wheel_version}-py3-none-any.whl"
    expected_sdist = f"snakemd_stubs-{wheel_version}.tar.gz"
    if wheel.name != expected_wheel or sdist.name != expected_sdist:
        raise ValueError(
            "artifact filenames do not match the verified project version: "
            f"expected {expected_wheel!r} and {expected_sdist!r}; "
            f"found {wheel.name!r} and {sdist.name!r}"
        )
    return wheel_version


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path, help="directory containing build artifacts")
    parser.add_argument("--tag", help="require this vMAJOR.MINOR.PATCH.STUB_REV tag version")
    args = parser.parse_args(argv)
    try:
        version = verify_artifacts(args.dist_dir, args.tag)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Verified {PROJECT_NAME} {version} wheel and sdist", file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
