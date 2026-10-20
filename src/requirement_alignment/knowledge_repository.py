"""Least-privilege Supabase REST knowledge reader.

Caller supplies a *verified* Supabase user JWT. Never accept a user ID or
tenant claim from client JSON. Queries run with the caller JWT (not service-role)
so PostgreSQL RLS remains in force. This module does not implement uploads.
"""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pydantic import BaseModel, Field


class KnowledgeAccessError(RuntimeError):
    pass


class KnowledgeReaderConfig(BaseModel):
    url: str = Field(pattern=r"^https://")
    publishable_key: str = Field(min_length=1)


class SupabaseKnowledgeReader:
    def __init__(self, config: KnowledgeReaderConfig, transport=None):
        self.config = config
        self.transport = transport or self._http_transport

    @staticmethod
    def _http_transport(url: str, headers: dict[str,str]):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=12) as result:
                return json.loads(result.read())
        except HTTPError as exc:
            raise KnowledgeAccessError(f"Supabase read failed (HTTP {exc.code})") from None

    def search_documents(self, jwt: str, organization_id: str, *, limit: int = 20):
        if not jwt or not jwt.strip() or not 1 <= limit <= 50:
            raise ValueError("authenticated JWT and bounded limit required")
        if not organization_id:
            raise ValueError("organization_id required")
        params = urlencode({
            "select": "id,title,kind,visibility,source_name,version",
            "organization_id": f"eq.{organization_id}",
            "state": "eq.READY",
            "limit": str(limit),
        })
        headers = {
            "apikey": self.config.publishable_key,
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/json",
        }
        # RLS policy enforces membership and explicit document ACL.
        return self.transport(f"{self.config.url.rstrip('/')}/rest/v1/kb_documents?{params}",headers)
