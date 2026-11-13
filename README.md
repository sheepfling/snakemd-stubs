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

`pyproject.toml` owns verification dependencies as PEP 735 groups: `dev` for
native checker and documentation tools, and `target` for the exact runtime and
consumer checks. Hosted CI installs these groups only; it never installs or
invokes Alphus. The dependency groups use PEP 735 support in current pip. The
shared CI runner upgrades pip before installing them.

```shell
python3.12 -m tests.run_ci
```

This runs the complete Python 3.10–3.15 matrix. Install those interpreters and
make `python3.10` through `python3.15` available on `PATH`; the runner creates
temporary checker and target environments outside the checkout, installs the
`dev` and `target` groups, and removes the environments when it finishes. To
run one matrix leg, pass its interpreter path:

```shell
python3.12 -m tests.run_ci --target-python /path/to/python3.12
```

Hosted CI calls this same runner once per matrix leg, so local and hosted runs
use the same build, lint, typing, runtime, and packaging commands.

The native typing-fixture runner validates the fixture configuration, requires
fixture paths to stay inside the repository, and checks both positive and
expected-negative calls under MyPy, Pyright, and ty. Pytest covers valid and
invalid configuration values; the runtime smoke keeps package-specific behavior in a
separate `main()` entry point. CI explicitly requires all three checker entries
in `stub-quality.json`, so removing one fails the run instead of skipping it.

This is the ordinary native development and test setup. It selects only the
`dev` and `target` groups and does not request Alphus. For an experimental
maintainer-side audit, install the separately named `dev-experimental` group
in a separate environment:

```shell
python -m pip install --group dev-experimental
alphus --root . --config quality-gates.toml --run --profile check
```

The `dev-experimental` group is excluded from the ordinary pip install above
and from hosted CI. It contains a Git dependency and may be unavailable when
Git access is blocked. uv resolves all declared dependency groups when creating
or refreshing a lockfile, even when a later sync selects only `dev`; therefore
`uv lock` may require Git access to this experimental group. uv was not
available in the validation environment, so its behavior was not tested here.
See uv's [dependency-group resolution] documentation and [automatic lock
behavior].

[dependency-group resolution]: https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups
[automatic lock behavior]: https://docs.astral.sh/uv/concepts/projects/sync/#automatic-lock-and-sync

The project owns `quality-gates.toml`; it calls Alphus's existing rules rather
than copying their implementations. Alphus's installed CLI entry points provide
the shared verification tools. `snakemd-stubs` uses
Alphus only as a development tool. The compatibility command builds both
distributions from a temporary source copy, installs the wheel, and runs the
runtime inventory, strict positive and expected-negative consumer probes,
stubtest, and a runtime smoke through a consumer directory outside the source
checkout.

```shell
alphus-stub-quality \
  --root . --config stub-quality.json --with-twine
```

The optional `dev-experimental` group is separate from both native CI groups.
Shared tool configuration is documented in [Alphus's stub-package CI
guide][alphus-ci].

[alphus-ci]: https://github.com/sheepfling/alphus/blob/b4b6055a6ae0286912b461cd2b4262b3318c5a0c/docs/STUB-PACKAGE-CI.md

Hosted CI is independent of Alphus while Alphus is unpublished on PyPI. The
PR/manual workflow uses six Python targets (3.10–3.15) and invokes
`tests.run_ci` for each one. The runner creates a Python 3.12 checker
environment and an isolated target environment. It runs Ruff lint/format,
Mypy on the fixture runner, mdrepo and rumdl on the 3.12 leg; every target builds
and installs the stub wheel, checks positive and expected-negative
MyPy/Pyright/ty consumer fixtures, runs native stubtest and the runtime smoke,
and validates the distributions with Twine. Locally, the same command runs all
six targets when their interpreters are available. Python 3.15 is a configured
compatibility target. A local CPython 3.15.2 check also passed the
installed-wheel consumer typing fixtures and runtime smoke against SnakeMD
2.4.1; this does not establish a hosted matrix run, change support metadata, or
prove every release in the supported range. Alphus's
runtime-to-stub API inventory audit remains available in the optional local
profile and is omitted from hosted CI until the shared tooling is published.
Opening, reopening, or updating a PR targeting `main` triggers this workflow;
manual dispatch is also available. The exact
SnakeMD runtime baseline for consumer checks is `SnakeMD==2.4.1` in the
`target` dependency group.

Before release, also check every SnakeMD release inside the supported runtime
range. Provision each selected runtime into each target venv and invoke the
checker with `--target-python` as shown below. The routine matrix establishes
only the exact pinned runtime; structural parity and smoke cases do not prove
all runtime behavior or untested releases.

Dependabot checks SnakeMD weekly and limits version updates to one open pull
request. The exact compatibility pin makes new releases inside the supported
`>=2.4,<2.5` range visible to CI without expanding the routine runtime matrix.

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

After the release commit has passed the merged-PR CI, create and push an
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

### Shared verification tooling

The reusable example runner and AST/API assertions come from the reviewed
Alphus revision. Install it only for an experimental audit in a dedicated
Python 3.11+ verification environment; the Git dependency is isolated in the
`dev-experimental` group and is not used by native development or CI:

```shell
python -m pip install --upgrade pip
python -m pip install --group dev --group target
python -m pip install --group dev-experimental
alphus-stub-quality --root . --config stub-quality.json --with-twine
```

For an unpublished local candidate, install its built Alphus wheel instead of
the Git requirement. The consumer wheel has no Alphus runtime dependency.
Alphus and native Mypy/Pyright/ty run in a Python 3.11+ checker environment.
Build/install, API audit, native stubtest and smoke execute in a distinct target
venv. The target does not install Alphus. For example, after provisioning the
checker as above, use a Python 3.10 target:

```shell
python -m pip install --upgrade pip
python3.10 -m venv /path/to/target
/path/to/target/bin/python -m pip install --group target
export ALPHUS_TARGET_PYTHON=/path/to/target/bin/python
alphus-stub-quality --root . --config stub-quality.json \
  --with-twine --target-python /path/to/target/bin/python --report target-result.json
```

Repeat with each Python target 3.10–3.15. All three native type checkers explicitly
select that target's packages and language version; the JSON report records
checker/target identities and each executed stage. Failed target checks stop the
run without falling back to the checker.

### Consumer profiles

The `check` profile composes `stubs`, `python`, and `markdown`. Run the complete
selection with the installed pinned Alphus tooling:

```shell
alphus --root . --config quality-gates.toml --run --profile check
```

Use `--profile stubs`, `--profile python`, or `--profile markdown` to run one
part. The stub stage builds and installs the wheel before later tooling runs.
These instructions are for optional local verification. Hosted CI does not
install the Git-based Alphus pin or call its actions; it uses the repository's
native Python tools and fixture runner until Alphus is published on PyPI.
The installed-wheel API audit is therefore a local optional gate, while native
stubtest, consumer fixtures, and runtime smoke remain in the merged/manual CI
workflow.

### Standalone package checks

See [package artifact checks](docs/PACKAGE-CHECKS.md) for a reusable wheel/sdist
validation command and real-build corruption regressions. Existing native CI
already checks artifact parity; this command provides an independent entry point
for local checks and future shared-runner integration.
