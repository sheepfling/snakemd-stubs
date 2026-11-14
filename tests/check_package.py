"""Build and validate SnakeMD's package-owned wheel/sdist version contract."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from tests.verify_release_artifacts import verify_artifacts

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="snakemd-artifacts-") as temporary:
        artifacts = Path(temporary) / "dist"
        try:
            result = subprocess.run(
                [sys.executable, "-m", "build", "--outdir", str(artifacts)],
                cwd=ROOT,
                check=False,
            )
            if result.returncode:
                return result.returncode
            version = verify_artifacts(artifacts)
        except (OSError, ValueError) as error:
            print(f"Package artifact validation failed: {error}", file=sys.stderr)
            return 1
    print(f"Verified snakemd-stubs {version} wheel/sdist version parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
