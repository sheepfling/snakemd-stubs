# snakemd-stubs

PEP 561 type stubs for [SnakeMD](https://github.com/TheRenegadeCoder/SnakeMD),
the Markdown-generation library for Python.

## Supported versions

The first release targets the SnakeMD 2.4 API:

- first tag: `v2.4.1.0`
- runtime dependency: `SnakeMD>=2.4.0,<2.5.0`
- Python: `>=3.10,<4.0`

SnakeMD 2.4.0 and 2.4.1 expose the same public API. SnakeMD 2.3.x is
intentionally outside this package's range because 2.4 introduced
`Alert`, `Checklist`, and the `Inline.breakline()` API, while also changing
list internals.

The version format is `RUNTIME_MAJOR.RUNTIME_MINOR.RUNTIME_PATCH.STUB_REV`.
The first three components identify the runtime API line; the final component
increments when the stubs are corrected or expanded without changing the
supported SnakeMD runtime range.

Each release line has one runtime dependency range. For example, a future
`2.3.x.y` line would require `SnakeMD>=2.3,<2.4`, while a `2.5.x.y` line would
require `SnakeMD>=2.5,<2.6`. The latest API line is maintained on `main`; an
older line receives a `release/<major>.<minor>` branch only when it needs a
correction.

Versions are derived from Git tags with `setuptools-scm`. Release tags use the
form `vRUNTIME_MAJOR.RUNTIME_MINOR.RUNTIME_PATCH.STUB_REV`; do not edit a
version string in `pyproject.toml`.

## Installation

```shell
python -m pip install snakemd-stubs
```

The runtime package is declared as a dependency, as recommended for a
standalone PEP 561 stub distribution. The stubs are used automatically by
type checkers after installation; application imports remain `import snakemd`.

## Scope

The declarations cover the public classes and convenience methods exported by
SnakeMD's `snakemd`, `snakemd.document`, `snakemd.elements`, and
`snakemd.templates` modules. They are based on the existing declarations in
[`GitHub-Org-Observer/typings/snakemd`](https://github.com/sheepfling/GitHub-Org-Observer/tree/main/typings/snakemd)
and checked against the published SnakeMD 2.4.0 and 2.4.1 source archives.

## Releasing

CI validates formatting, type checking, runtime/stub compatibility, and both
PyPI artifacts. To release, commit the changes, create a matching version tag
(for example, `v2.4.1.0`), and push the tag. The publish workflow uses PyPI
Trusted Publishing; configure the PyPI project to trust this repository's
`publish.yml` workflow before pushing the first release tag.

## License

The stubs are distributed under the MIT License. See `LICENSE`.
