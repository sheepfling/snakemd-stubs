# snakemd-stubs

PEP 561 type stubs for [SnakeMD](https://github.com/TheRenegadeCoder/SnakeMD),
the Markdown-generation library for Python.

## Supported versions

The first release targets the SnakeMD 2.4 API:

- first tag: `v2.4.1.0`
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
invokes Alphus. The dependency groups use the PEP 735 support in current pip;
CI upgrades pip before installing them.

```shell
python -m pip install --upgrade pip
python -m pip install --group dev --group target
```

This is the ordinary native development and test setup. It selects only the
`dev` and `target` groups and does not request Alphus. For an experimental
maintainer-side audit, install the pinned Alphus Git revision directly in a
separate environment; this optional tool is deliberately not declared in
`pyproject.toml`:

```shell
python -m pip install "alphus @ git+https://github.com/sheepfling/alphus.git@b4b6055a6ae0286912b461cd2b4262b3318c5a0c"
alphus --root . --config quality-gates.toml --run --profile check
```

Because the Alphus Git URL is not in project metadata or dependency groups,
uv's project lock and sync commands have no Alphus source to resolve. uv is not
installed in the validation environment, so that behavior was assessed from
the repository metadata and uv documentation, not tested directly. uv resolves
all declared dependency groups when creating a lockfile and may lock before
sync/run if the lock is absent or stale; keeping Alphus outside the project
dependency graph prevents those normal project operations from requesting it.
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

The optional direct Alphus install is separate from both native CI groups.
Shared tool configuration is documented in [Alphus's stub-package CI
guide][alphus-ci].

[alphus-ci]: https://github.com/sheepfling/alphus/blob/b4b6055a6ae0286912b461cd2b4262b3318c5a0c/docs/STUB-PACKAGE-CI.md

Hosted CI is independent of Alphus while Alphus is unpublished on PyPI. The
merged-PR/manual workflow uses six Python targets (3.10–3.15), with
a separate Python 3.12 checker environment and isolated runtime targets. It
runs Ruff lint/format, Mypy on the native consumer helpers, mdrepo and rumdl on
the 3.12 leg; every target builds and installs the stub wheel, checks positive
and expected-negative MyPy/Pyright consumer fixtures, runs native stubtest and
the runtime smoke, and validates the distributions with Twine. Python 3.15
is a configured compatibility target; it does not change the package's support
metadata or establish a local 3.15 result. Alphus's
runtime-to-stub API inventory audit remains available in the optional local
profile and is omitted from hosted CI until the shared tooling is published.
Opening or pushing a PR branch does not trigger this workflow. The exact
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

To release, commit the changes, create a matching version tag (for example,
`v2.4.1.0`), and push the tag. The publish workflow uses PyPI Trusted
Publishing; configure the PyPI project to trust this repository's `publish.yml`
workflow before pushing the first release tag.

## License

The stubs are distributed under the MIT License. See `LICENSE`.

### Shared verification tooling

The reusable example runner and AST/API assertions come from the reviewed
Alphus revision. Install it only for an experimental audit in a dedicated
Python 3.11+ verification environment; the Git dependency is intentionally
outside `pyproject.toml` so native development setup and project locking do not
resolve it:

```shell
python -m pip install --upgrade pip
python -m pip install --group dev --group target
python -m pip install "alphus @ git+https://github.com/sheepfling/alphus.git@b4b6055a6ae0286912b461cd2b4262b3318c5a0c"
alphus-stub-quality --root . --config stub-quality.json --with-twine
```

For an unpublished local candidate, install its built Alphus wheel instead of
the Git requirement. The consumer wheel has no Alphus runtime dependency.
Alphus and native Mypy/Pyright run in a Python 3.11+ checker environment.
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

Repeat with each Python target 3.10–3.15. Both native static checkers explicitly
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
