"""Keep the installed-runtime consumer probe in the native pytest suite."""

from tests.runtime_smoke import main


def test_runtime_smoke() -> None:
    main()
