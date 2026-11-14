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
compatibility checks use the exact runtime pin in the `target` dependency group.
Additional runtime releases inside the supported range are checked in separate
release-only environments.

## Audit and consumer checks

`tests/audit_api_coverage.py` compares the installed stub distribution with the
installed SnakeMD runtime. It checks the facade exports and module-owned
definitions, signatures and defaults, annotations, decorators, base classes,
enum members, and public attributes. It also preserves the distinction between
the supported facade and runtime implementation bindings.

`tests/typecheck.py` exercises the supported API with positive consumer calls.
The negative fixture verifies that unsupported names, values, and abstract
class instantiations are rejected by Mypy, Pyright, and ty. The runtime smoke
executes the consumer fixture and checks that rendered output can be written;
stubtest compares the installed stub wheel with the runtime.

The annotations have three narrow accommodations that reflect runtime behavior:

These are explicit differences from the runtime's own annotations: its two
path parameters are declared as `str` even though the implementations pass
them to `open`, which accepts path-like values; and `Inline.get_link` is
annotated as `str` even though an unlinked instance returns `None`.

- `Document.add_table_from_csv(path: str | os.PathLike[str]) -> CSVTable` accepts
  path-like inputs because its implementation passes `path` to `open`.
- `CSVTable.__init__(path: str | os.PathLike[str], encoding="utf-8") -> None`
  has the same accommodation.
- `Inline.get_link() -> str | None` can return `None` for an unlinked `Inline`,
  despite the runtime's `str` annotation.

The audit allows these exact differences and keeps its other signature and
annotation checks strict.

## Run and limits

Prepare separate checker and target environments using the
[development instructions](../DEVELOPMENT.md), then run from the repository root:

```shell
.venv-checker/bin/python -m tests.ci target \
  --target-python .venv-target/bin/python --report target-result.json
```

The shared gate builds distributions from a temporary source copy, installs the
wheel, and runs the API audit and consumer checks outside the checkout. Generic
verification lives in Alphus; API expectations and fixtures stay here. Hosted
CI runs this audit for every configured Python target, followed by the native
fixture parity lane. The package-owned artifact validator runs separately on
Python 3.12. Before release, repeat these checks in clean environments for the
declared Python versions and supported runtime releases.

These checks provide structural API, type-checking, and selected runtime
evidence. They do not prove every Markdown rendering behavior or error case.
