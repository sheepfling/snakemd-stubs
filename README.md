# snakemd-stubs

PEP 561 type stubs for [SnakeMD](https://github.com/TheRenegadeCoder/SnakeMD),
the Markdown-generation library for Python.

## Supported versions

The first release targets the SnakeMD 2.4 API:

- first release tag: `v2.4.1.0`
- runtime dependency: `SnakeMD>=2.4.0,<2.5.0`
- Python: `>=3.10,<4.0`

The runtime range excludes SnakeMD 2.3.x because the 2.4 API introduced
`Alert`, `Checklist`, and `Inline.breakline()`, and changed list internals.

The version format is `RUNTIME_MAJOR.RUNTIME_MINOR.RUNTIME_PATCH.STUB_REV`.
The first three components identify the runtime API line; the final component
increments when the stubs are corrected or expanded without changing the
supported SnakeMD runtime range.

Each release line has one runtime dependency range. For example, a future
`2.3.x.y` line would require `SnakeMD>=2.3,<2.4`, while a `2.5.x.y` line would
require `SnakeMD>=2.5,<2.6`. The latest API line is maintained on `main`; an
older line receives a `release/<major>.<minor>` branch only when it needs a
correction.

Versions are derived from Git tags with `setuptools-scm`. Stable release tags
use the form `vRUNTIME_MAJOR.RUNTIME_MINOR.RUNTIME_PATCH.STUB_REV`; do not edit
a version string in `pyproject.toml`. After a tag, development builds use the
next stub revision with a `.devN` suffix. For example, commits after
`v2.4.1.0` report versions like `2.4.1.1.dev23`; building the exact tag reports
`2.4.1.0`.

## Installation

```shell
python -m pip install snakemd-stubs
```

The runtime package is declared as a dependency, as recommended for a
standalone PEP 561 stub distribution. The stubs are used automatically by
type checkers after installation; application imports remain `import snakemd`.

## Scope

The supported API is the public class/function facade exported from `snakemd`
and public definitions owned by `snakemd.document`, `snakemd.elements`, and
`snakemd.templates`. Imported helpers in those runtime modules are implementation
details, not additional supported API. See the [API coverage contract](docs/API-COVERAGE.md)
for the audit scope and limits.

The declarations began from the existing
[`GitHub-Org-Observer/typings/snakemd`](https://github.com/sheepfling/GitHub-Org-Observer/tree/main/typings/snakemd)
definitions and are audited against the installed runtime source and wheel.

## Verification

See [Development and verification](DEVELOPMENT.md) for the common pinned
Alphus v0.0.3 workflow, separate checker/target environments, and the Python
3.10–3.15 matrix. Shared gates own the repeated checking mechanisms. The
package retains its public API inventory, runtime assertions, allowlist and
release-version validation. Native fixture checks remain a transitional
parity lane until the shared contract covers their boundary checks.

## Releasing

The published baseline is `2.4.1.0` (`v2.4.1.0`). For stub-only fixes against
the same SnakeMD baseline, increment the final component; the next such release
is `v2.4.1.1`. When targeting a new SnakeMD baseline, update the dependency
range if its supported API line changes, use the tested runtime version in the
first three components, and reset the stub revision to zero.

Release tags must be exact four-part tags such as `v2.4.1.1`. The publish
workflow builds from the tag, checks that it has this shape, and verifies that
the wheel filename, sdist filename, and both package metadata versions match
the tag before uploading. Local CI runs the same artifact check without a tag
to ensure the wheel and sdist agree on a valid four-part version.

After the release commit has passed the candidate CI, create and push an
annotated tag for that commit. Before the next tag push, configure the PyPI
project's Trusted Publisher for this repository's `publish.yml` workflow. To
tag the next stub-only fix, for example:

```shell
git tag -a v2.4.1.1 -m "Release v2.4.1.1"
git push origin v2.4.1.1
```

To reproduce the tagged build locally, use a detached worktree at the tag:

```shell
git worktree add --detach /tmp/snakemd-stubs-release v2.4.1.1
cd /tmp/snakemd-stubs-release
python3.12 -m pip install build twine
python3.12 -m build
python3.12 -m tests.verify_release_artifacts dist --tag v2.4.1.1
python3.12 -m twine check dist/*
```

Change the example tag and worktree path to the version being released.

## License

The stubs are distributed under the MIT License. See `LICENSE`.

## Shared verification tooling

[Alphus's v0.0.3 guide](https://github.com/sheepfling/alphus/blob/v0.0.3/docs/STUB-PACKAGE-CI.md)
describes the shared execution and evidence contracts. The `dev-experimental`
group remains as a compatibility alias; ordinary `dev` now includes Alphus.

### Standalone package checks

See [package artifact checks](docs/PACKAGE-CHECKS.md) for the standalone
wheel/sdist validation command and real-build corruption regressions. The
package-owned CI lane runs this command once on Python 3.12.
