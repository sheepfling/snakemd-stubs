"""Exercise the package lane against real build outputs, including corruption."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from tests import check_package


@pytest.fixture(scope="module")
def built_artifacts(tmp_path_factory: pytest.TempPathFactory) -> Path:
    artifacts = tmp_path_factory.mktemp("real-artifacts") / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(artifacts)],
        cwd=check_package.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return artifacts


def _change_sdist_version(artifact: Path) -> None:
    members: list[tuple[tarfile.TarInfo, bytes | None]] = []
    with tarfile.open(artifact, "r:gz") as archive:
        for member in archive.getmembers():
            stream = archive.extractfile(member) if member.isfile() else None
            data = stream.read() if stream is not None else None
            if data is not None and member.name.endswith("PKG-INFO"):
                lines = data.decode().splitlines(keepends=True)
                data = "".join(
                    "Version: 9.9.9.9\n" if line.startswith("Version: ") else line for line in lines
                ).encode()
                member.size = len(data)
            members.append((member, data))
    with tarfile.open(artifact, "w:gz") as archive:
        for member, data in members:
            archive.addfile(member, io.BytesIO(data) if data is not None else None)


@pytest.mark.parametrize("damage", [None, "version", "missing", "extra"])
def test_package_lane_validates_real_build_outputs(
    monkeypatch: pytest.MonkeyPatch,
    built_artifacts: Path,
    damage: str | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def build(command: list[str], *, cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
        assert command[:4] == [sys.executable, "-m", "build", "--outdir"]
        assert cwd == check_package.ROOT and check is False
        artifacts = Path(command[4])
        shutil.copytree(built_artifacts, artifacts)
        if damage == "version":
            _change_sdist_version(next(artifacts.glob("*.tar.gz")))
        elif damage == "missing":
            next(artifacts.glob("*.whl")).unlink()
        elif damage == "extra":
            (artifacts / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("tests.check_package.subprocess.run", build)
    assert check_package.main() == (0 if damage is None else 1)
    output = capsys.readouterr()
    if damage == "version":
        assert "does not match sdist version 9.9.9.9" in output.err
    elif damage in {"missing", "extra"}:
        assert "expected exactly one wheel and one .tar.gz sdist" in output.err


def test_package_lane_preserves_build_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "tests.check_package.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 7),
    )
    assert check_package.main() == 7
