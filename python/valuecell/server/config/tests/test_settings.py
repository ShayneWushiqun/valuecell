from valuecell.server.config import settings as settings_module


def test_build_mysql_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_USER", "tester")
    monkeypatch.setenv("DB_PASSWORD", "p@ss word")
    monkeypatch.setenv("DB_NAME", "valuecell_test")

    database_url = settings_module._build_mysql_database_url()

    assert database_url == (
        "mysql+pymysql://tester:p%40ss+word@127.0.0.1:3307/valuecell_test"
    )


def test_get_csv_env(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEYS", "a, b ,,c ")

    values = settings_module._get_csv_env("TAVILY_API_KEYS")

    assert values == ["a", "b", "c"]
