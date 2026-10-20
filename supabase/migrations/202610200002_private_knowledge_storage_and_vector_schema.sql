-- Applied to development project qgpulwddylrnpigqeykt on 2026-10-20.
-- Move pgvector out of exposed public schema and provision private bucket.
create schema if not exists extensions;
alter extension vector set schema extensions;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values (
  'enterprise-knowledge-private',
  'enterprise-knowledge-private',
  false,
  20971520,
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain'
  ]
) on conflict (id) do nothing;
