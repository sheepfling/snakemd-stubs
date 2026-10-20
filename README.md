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

Use a Python 3.11+ verification environment. Install the package's development
tools, pinned Alphus tooling and exact runtime pin into it. The `dev` extra
centralizes the local verification
tools; hosted CI separates repository quality from target compatibility.

```shell
python -m pip install ".[dev]" -r requirements-compat.txt
python -m pip install -r requirements-quality.txt
```

The full local profile uses Alphus as the configured orchestrator, plus the
available `mdrepo` and `rumdl` tools for Markdown links/graph and style. Install
Alphus from its checked-out package as described in its README, then run:

```shell
alphus --root . --config quality-gates.toml --run --profile check
```

The project owns `quality-gates.toml`; it calls Alphus's existing rules rather
than copying their implementations. The shared verification tools also
ship in the Alphus wheel and are invoked as a module. `snakemd-stubs` uses
Alphus only as a development tool. The compatibility command builds both
distributions from a temporary source copy, installs the wheel, and runs the
runtime inventory, strict positive and expected-negative consumer probes,
stubtest, and a runtime smoke through a consumer directory outside the source
checkout.

```shell
python -m alphus_stub_quality.verify \
  --root . --config stub-quality.json --with-twine
```

Install the pinned Alphus wheel in the verification environment before this
command. The
shared tool configuration and GitHub Action are documented in
[Alphus's stub-package CI guide](https://github.com/sheepfling/alphus/blob/main/docs/STUB-PACKAGE-CI.md).

Hosted CI separates one repository-quality job from installed-wheel target
compatibility on Python 3.10–3.14, with a Python 3.12 checker. Triggers remain
merged PRs against `main` and manual dispatch. Opening a PR or pushing its branch
does not trigger these jobs. The exact runtime baseline is
`requirements-compat.txt`.

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
Alphus revision recorded in `requirements-quality.txt`. Install that tooling
in a dedicated Python 3.11+ verification environment:

```shell
python -m pip install -r requirements-quality.txt
python -m alphus_stub_quality.verify --root . --config stub-quality.json --with-twine
```

For an unpublished local candidate, install its built Alphus wheel instead of
the Git requirement. The consumer wheel has no Alphus runtime dependency.
Alphus and native Mypy/Pyright run in a Python 3.11+ checker environment.
Build/install, API audit, native stubtest and smoke execute in a distinct target
venv. The target does not install Alphus. For example, after provisioning the
checker as above, use a Python 3.10 target:

```shell
python3.10 -m venv /path/to/target
/path/to/target/bin/python -m pip install -r requirements-target.txt \
  -r requirements-compat.txt
python -m alphus_stub_quality.verify --root . --config stub-quality.json \
  --with-twine --target-python /path/to/target/bin/python --report target-result.json
```

Repeat with each Python target 3.10–3.14. Both native static checkers explicitly
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
Hosted CI runs `quality` (`python` plus `markdown`) once and the shared
`ci/stub-quality` action once per target 3.10–3.14, using checker Python 3.12.
It runs only after a merged PR or manual dispatch. Both action references and
`requirements-quality.txt` pin the same immutable Alphus commit. Each
repository retains its native tool settings, examples and API expectations;
Alphus owns the repeated checking mechanisms and their regression tests.
