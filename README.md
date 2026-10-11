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

The supported API is the class/function facade exported from `snakemd`, plus
the classes and methods owned by `snakemd.document`, `snakemd.elements`, and
`snakemd.templates`. Their unprefixed imported helpers are implementation
bindings, not added to the supported API just because the runtime modules lack
`__all__`. The coverage inventory records those runtime namespace bindings
separately and checks them for changes. See [API coverage evidence](docs/API-COVERAGE.md)
for the exact surface and audit limits.

The declarations began from the existing
[`GitHub-Org-Observer/typings/snakemd`](https://github.com/sheepfling/GitHub-Org-Observer/tree/main/typings/snakemd)
definitions and are audited against the installed runtime source and wheel.

## Verification

Install the verification tools and the currently pinned runtime into the
active virtual environment. This installs tools only; the compatibility
command builds the project from a temporary copy outside the checkout.

```shell
python -m pip install -r requirements-compat.txt \
  "build>=1.2" "mypy>=2.3" "pyright>=1.1.414" \
  "setuptools>=80" "setuptools-scm>=9.2" "twine>=7.0" "wheel"
```

The full local profile uses Alphus as the configured orchestrator, plus the
available `mdrepo` and `rumdl` tools for Markdown links/graph and style. Install
Alphus from its checked-out package as described in its README, then run:

```shell
alphus --root . --config quality-gates.toml --run --profile check
```

The project owns `quality-gates.toml`; it calls Alphus's existing rules rather
than copying their implementations. The compatibility command builds both
distributions from a temporary source copy, installs the wheel, and runs the
runtime inventory, strict positive and expected-negative consumer probes,
stubtest, and a runtime smoke through a consumer directory outside the source
checkout. Run it directly with `--with-twine` if Alphus is not installed.

Hosted CI remains one Ubuntu/Python 3.12 job after a pull request is merged to
`main`, with manual dispatch available. It runs the same build and compatibility
command without the optional Twine step. It uses the exact runtime pin in
`requirements-compat.txt`; opening a PR and direct pushes do not add routine
hosted runs.

Before a release, run the release-only matrix across Python 3.10–3.14 and every
published SnakeMD version in `>=2.4.0,<2.5.0` (currently 2.4.0 and 2.4.1). For
each Python environment, install the dev tools and runtime, then run the
compatibility command once per runtime version:

```shell
for python in python3.10 python3.11 python3.12 python3.13 python3.14; do
  venv="$(mktemp -d)"
  "$python" -m venv "$venv"
  "$venv/bin/python" -m pip install \
    "build>=1.2" "mypy>=2.3" "pyright>=1.1.414" \
    "setuptools>=80" "setuptools-scm>=9.2" "twine>=7.0" "wheel" \
    "SnakeMD==2.4.0"
  "$venv/bin/python" tests/verify_compatibility.py --with-twine
  "$venv/bin/python" -m pip install --force-reinstall --no-deps "SnakeMD==2.4.1"
  "$venv/bin/python" tests/verify_compatibility.py --with-twine
  rm -rf "$venv"
done
```

Routine CI proves one current runtime on Python 3.12. The release matrix is the
separate evidence for the broader declared Python/runtime support; neither
structural API matching nor a consumer smoke proves full behavioral semantics.

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
