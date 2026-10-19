"""Supabase connection configuration; deliberately no implicit production access.

The service role key must never be placed in the browser or git repository.
Production ingestion requires server-verified identity and document ACL checks.
"""
from pydantic import BaseModel, SecretStr, ConfigDict


class SupabaseSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    service_role_key: SecretStr
    bucket: str = "enterprise-knowledge-private"

    def __repr__(self) -> str:
        return f"SupabaseSettings(url={self.url!r}, bucket={self.bucket!r}, service_role_key=<redacted>)"


def required_supabase_settings(env: dict[str, str]) -> SupabaseSettings:
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError("Missing Supabase server configuration: " + ", ".join(missing))
    return SupabaseSettings(
        url=env["SUPABASE_URL"].rstrip("/"),
        service_role_key=env["SUPABASE_SERVICE_ROLE_KEY"],
        bucket=env.get("SUPABASE_KNOWLEDGE_BUCKET") or "enterprise-knowledge-private",
    )
