import pytest
from requirement_alignment.supabase_config import required_supabase_settings


def test_missing_secrets_fail_closed():
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        required_supabase_settings({})


def test_settings_do_not_echo_key():
    s = required_supabase_settings({"SUPABASE_URL":"https://example.supabase.co/",
                                    "SUPABASE_SERVICE_ROLE_KEY":"extremely-secret-value"})
    assert s.url == "https://example.supabase.co"
    assert "extremely-secret-value" not in repr(s)
