"""Compatibility entry point; prepare environments as described in DEVELOPMENT.md."""

from __future__ import annotations

import sys

from tests.ci import main

if __name__ == "__main__":
    raise SystemExit(main(["target", *sys.argv[1:]]))
