from tools.hello import main


def test_import() -> None:
    assert callable(main)
