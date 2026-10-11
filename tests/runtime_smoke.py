"""Exercise the typed consumer probe against an installed SnakeMD runtime."""

from __future__ import annotations

import tempfile
from pathlib import Path

from typecheck import exercise_public_api


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="snakemd-runtime-smoke-") as temporary:
        root = Path(temporary)
        csv_path = root / "items.csv"
        csv_path.write_text("name,value\none,1\n", encoding="utf-8")
        output_dir = root / "rendered"
        output_dir.mkdir()

        rendered = exercise_public_api(csv_path, output_dir)
        written = (output_dir / "consumer-probe.md").read_text(encoding="utf-8")
        if rendered != written:
            raise SystemExit("Document.dump output differs from rendered Document text")
        for expected in ("initial block", "raw Markdown", "inline", "name", "sample block"):
            if expected not in rendered:
                raise SystemExit(f"runtime smoke output is missing {expected!r}")

    print("Runtime smoke executed every typed public constructor/method probe.")


if __name__ == "__main__":
    main()
