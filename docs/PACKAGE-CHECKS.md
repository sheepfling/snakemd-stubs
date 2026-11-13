# Package artifact checks

The existing native CI runner already validates built wheel and sdist versions.
For a standalone packaging check, prepare the development tools from the
repository root and run:

```shell
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --group dev
.venv/bin/python -m tests.check_package
```

On Windows, use `py -3.12` and `.venv\Scripts\python.exe` instead. The command
builds a fresh wheel and sdist in a temporary directory, then checks their
four-part versions, filenames, project names and package metadata agree.
Missing or extra artifacts, metadata disagreement and build failures fail the
command. Temporary artifacts are removed afterward. This command neither
creates release tags nor publishes packages; use the existing release workflow
and tag-aware validator for a release.

The package-owned command can be called independently by a future shared CI
adapter. It deliberately performs its own build, rather than claiming to check
artifacts retained by another tool. Existing native CI remains unchanged.

`tests/test_check_package.py` builds real artifacts without build isolation
using the installed development or target dependencies. It verifies acceptance
of valid outputs and rejection of altered sdist versions, missing wheels and
extra files, and confirms build errors propagate. The existing full pytest
suite runs these regressions on every supported Python target, 3.10 through
3.15. No network access is needed for that test build once dependencies exist.
