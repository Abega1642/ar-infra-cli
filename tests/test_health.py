from src.ar_infra.health import ping


def test_ping_returns_pong():
    """Test that ping() returns 'pong'"""
    result = ping()
    assert result == "pong"
