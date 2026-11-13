"""Exercise the thin repository adapter, not Alphus's checker implementation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests import ci


@pytest.mark.parametrize("exit_code", [0, 1, 124])
def test_target_preserves_shared_result_and_stops_after_failure(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    calls: list[list[str]] = []

    def run(
        argv: list[str], *, cwd: Path, check: bool, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        assert cwd == ci.ROOT
        assert check is False
        calls.append(argv)
        return subprocess.CompletedProcess(argv, exit_code)

    monkeypatch.setattr("tests.ci.subprocess.run", run)
    assert (
        ci.main(["target", "--target-python", "/target/python", "--report", "result.json"])
        == exit_code
    )
    assert calls[0][2] == "alphus.gates.stubs.verify"
    assert calls[0][-4:] == [
        "--target-python",
        "/target/python",
        "--report",
        "result.json",
    ]
    assert len(calls) == (2 if exit_code == 0 else 1)
    if exit_code == 0:
        assert calls[1] == ["/target/python", "-m", "pytest", "-q"]


def test_quality_uses_shared_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(
        argv: list[str], *, cwd: Path, check: bool, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        assert argv[2] == "alphus"
        assert argv[-3:] == ["--profile", "quality", "--run"]
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("tests.ci.subprocess.run", run)
    assert ci.main(["quality"]) == 0


def test_spawn_failure_is_not_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic spawn failure")

    monkeypatch.setattr("tests.ci.subprocess.run", fail)
    assert ci.main(["target", "--target-python", "/target/python"]) == 127


@pytest.mark.parametrize("original_path", [None, "", "/existing/tools"])
def test_child_tools_follow_selected_interpreter_without_mutating_parent(
    monkeypatch: pytest.MonkeyPatch, original_path: str | None
) -> None:
    if original_path is None:
        monkeypatch.delenv("PATH", raising=False)
    else:
        monkeypatch.setenv("PATH", original_path)
    monkeypatch.setenv("STUB_CI_TEST_VALUE", "preserved")
    parent = dict(os.environ)
    seen: list[str] = []

    def run(
        argv: list[str], *, cwd: Path, check: bool, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        scripts = str(Path(argv[0]).absolute().parent)
        assert env["PATH"] == os.pathsep.join(part for part in (scripts, original_path) if part)
        assert env["STUB_CI_TEST_VALUE"] == "preserved"
        assert os.environ == parent
        seen.append(scripts)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("tests.ci.subprocess.run", run)
    assert ci.main(["target", "--target-python", "/target/bin/python"]) == 0
    assert len(seen) == 2
    assert os.environ == parent
