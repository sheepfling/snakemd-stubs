# Development and verification

Use Python 3.12 for the checker environment and a separate target environment
for each supported Python 3.10–3.15 runtime. Alphus is pinned to Git tag
`v0.0.3` (`997e4641c25339dcf31a510c3122aa50f8309ef1`), not installed as a
runtime dependency of the stub distribution.

## Prepare environments

From the repository root, choose each target interpreter explicitly:

```shell
python3.12 -m venv .venv-checker
python3.10 -m venv .venv-target
.venv-checker/bin/python -m pip install --upgrade pip
.venv-target/bin/python -m pip install --upgrade pip
.venv-checker/bin/python -m pip install --group dev
.venv-target/bin/python -m pip install --group target
.venv-checker/bin/python -m tests.ci quality
.venv-checker/bin/python -m tests.ci target --target-python .venv-target/bin/python
```

On Windows use `py -3.12`, the chosen `py -3.X`, and each environment's
`Scripts/python.exe` instead of `bin/python`. Installations require access to
the configured package registry and the pinned Git repository, or verified
local artifacts. The runner does not download or create environments itself.
Repeat the target preparation and command for every supported interpreter.

The target group pins `SnakeMD==2.4.1`, while the supported runtime range is
`SnakeMD>=2.4.0,<2.5.0`. The Python 3.10–3.15 matrix tests only that pinned
runtime; test other supported SnakeMD releases before release. Dependabot
checks SnakeMD weekly on Monday at 09:00 UTC, with at most one open update PR.

## Shared and package-owned checks

`tests.ci` is a thin entry point. Alphus owns isolated build/install, dependency
checks, native MyPy/Pyright/ty fixture execution, native stubtest and configured
API/runtime adapters. The target command then runs this package's pytest suite.
Use `--report /path/to/report.json` to retain the Alphus evidence report. A
failed shared stage stops the command; omitted or unexecuted work is not passed.
Each child receives its selected interpreter's script directory first on PATH,
while other inherited environment settings and the parent environment stay unchanged.

`stub-quality.json` retains the runtime module, fixture paths, three selected
checkers, API inventory adapter, runtime smoke and reviewed allowlist. Negative
diagnostic expectations come from fixture markers and checker defaults, not
explicit diagnostic lists in this configuration.
Release/version checks and actual behavioral assertions remain package-owned.
The `quality` profile delegates source and documentation checks to native tools.

The earlier local fixture runners are retained during parity migration. Their
strict boundary tests must not be discarded until the shared implementation
provides equivalent coverage; the v0.0.3 negative checker matches basenames,
not an exact diagnostic path. Native validation remains an explicit additional
CI lane for now, not a claim of complete consolidation. To reproduce that lane:

```shell
.venv-checker/bin/python -m tests.check_typing_fixtures \
  --target-python .venv-target/bin/python \
  --require-checker mypy --require-checker pyright --require-checker ty
```

The required-checker flags fail if any configured checker is removed; skipping
a checker is not a complete three-checker pass.

GitHub retains each repository's existing triggers and permissions. Compatibility
jobs select targets explicitly; repository-only quality runs once on Python3.12.
No release or publication is implied by a successful local or CI run.

## SnakeMD artifact version contract

Run `.venv-checker/bin/python -m tests.check_package` after preparing the checker
environment. CI runs this package-owned lane once on Python 3.12. It builds a
fresh wheel and sdist, then verifies their four-part versions, filenames and all
package metadata agree. Alphus v0.0.3 does not expose its temporary artifacts to
a package hook, so this lane deliberately performs a separate build. Unit tests
of the validator do not replace validation of actual build outputs.
