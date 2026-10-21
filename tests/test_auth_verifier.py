import pytest
from requirement_alignment.auth_verifier import AuthConfiguration, SupabaseAuthVerifier, AuthenticationError

def test_server_verifies_token_with_auth_provider():
    captured = []
    def transport(url, headers):
        captured.append((url, headers))
        return {"id":"verified-user"}
    verifier = SupabaseAuthVerifier(AuthConfiguration(
        url="https://example.supabase.co", publishable_key="example-key"), transport=transport)
    assert verifier.verify("Bearer example-token") == "verified-user"
    assert captured[0][0].endswith("/auth/v1/user")
    assert captured[0][1]["Authorization"] == "Bearer example-token"

def test_reject_missing_or_invalid_token():
    verifier = SupabaseAuthVerifier(AuthConfiguration(
        url="https://example.supabase.co", publishable_key="example-key"))
    with pytest.raises(AuthenticationError):
        verifier.verify("")

def test_reject_empty_user_response():
    verifier = SupabaseAuthVerifier(AuthConfiguration(
        url="https://example.supabase.co", publishable_key="example-key"),
        transport=lambda url, headers: {})
    with pytest.raises(AuthenticationError):
        verifier.verify("Bearer example-token")
