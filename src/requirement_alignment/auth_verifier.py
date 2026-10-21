"""Verify Supabase user access tokens against Supabase Auth.

No local JWT decoding or trust in caller-supplied actor IDs. This is a
server-side authorization prerequisite for protected knowledge routes.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pydantic import BaseModel, Field


class AuthConfiguration(BaseModel):
    url: str = Field(pattern=r"^https://")
    publishable_key: str = Field(min_length=1)


class AuthenticationError(ValueError):
    pass


class SupabaseAuthVerifier:
    def __init__(self, config: AuthConfiguration, transport=None):
        self.config = config
        self.transport = transport or self._request

    @staticmethod
    def _request(url: str, headers: dict[str, str]):
        try:
            with urlopen(Request(url, headers=headers), timeout=10) as res:
                return json.loads(res.read())
        except (HTTPError, URLError, ValueError):
            raise AuthenticationError("Supabase user verification failed") from None

    def verify(self, authorization: str) -> str:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthenticationError("Bearer access token required")
        user = self.transport(
            f"{self.config.url.rstrip('/')}/auth/v1/user",
            {"apikey": self.config.publishable_key,
             "Authorization": f"Bearer {token.strip()}",
             "Accept": "application/json"},
        )
        if not isinstance(user, dict) or not isinstance(user.get("id"), str) or not user["id"]:
            raise AuthenticationError("Invalid authenticated user")
        return user["id"]
