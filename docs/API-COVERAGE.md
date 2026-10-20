# API coverage contract

This document records the supported surface and the guarantees of the checks.
The executable audit is the source of truth for the runtime's names and
signatures; this contract avoids duplicating a version-specific API inventory.

## Supported API

The package supports the public class and function facade exported by
`snakemd`, together with public definitions owned by `snakemd.document`,
`snakemd.elements`, and `snakemd.templates`. Imported helper bindings in those
modules are implementation details, not additional supported API.

The package metadata declares the supported Python and SnakeMD ranges. Routine
compatibility checks use the exact runtime pin in `requirements-compat.txt`.
Additional runtime releases inside the supported range are checked as part of
the release-only compatibility matrix.

## Audit and consumer checks

`tests/audit_api_coverage.py` compares the installed stub distribution with the
installed SnakeMD runtime. It checks the facade exports and module-owned
definitions, signatures and defaults, annotations, decorators, base classes,
enum members, and public attributes. It also preserves the distinction between
the supported facade and runtime implementation bindings.

`tests/typecheck.py` exercises the supported API with positive consumer calls.
The negative fixture verifies that unsupported names, values, and abstract
class instantiations are rejected by both Mypy and Pyright. The runtime smoke
executes the consumer fixture and checks that rendered output can be written;
stubtest compares the installed stub wheel with the runtime.

The annotations have three narrow accommodations that reflect runtime behavior:

- `Document.add_table_from_csv(path: str | os.PathLike[str]) -> CSVTable` accepts
  path-like inputs because its implementation passes `path` to `open`.
- `CSVTable.__init__(path: str | os.PathLike[str], encoding="utf-8") -> None`
  has the same accommodation.
- `Inline.get_link() -> str | None` can return `None` for an unlinked `Inline`,
  despite the runtime's `str` annotation.

The audit allows these exact differences and keeps its other signature and
annotation checks strict.

## Run and limits

Run the compatibility check from the repository root after installing the
development extra and a supported SnakeMD release:

```shell
python -m tests.verify_compatibility --with-twine
```

It builds distributions from a temporary source copy, installs the wheel, and
runs the audit and consumer checks outside the checkout. Hosted CI runs the
same compatibility command on its configured Python version and exact runtime
pin. Before release, run the command in clean environments for the declared
Python versions and the supported runtime releases.

These checks provide structural API, type-checking, and selected runtime
evidence. They do not prove every Markdown rendering behavior or error case.
