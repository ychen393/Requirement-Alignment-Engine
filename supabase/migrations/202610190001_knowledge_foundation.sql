-- Private enterprise knowledge foundation. Apply only to a dedicated Supabase DEV project.
create extension if not exists pgcrypto;
create extension if not exists vector;

create table public.kb_organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check(length(trim(name))>0),
  created_at timestamptz not null default now()
);
create table public.kb_memberships (
  organization_id uuid not null references public.kb_organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check(role in ('owner','editor','viewer')),
  primary key (organization_id,user_id)
);
create table public.kb_projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.kb_organizations(id) on delete cascade,
  title text not null,
  created_at timestamptz not null default now(),
  unique(id,organization_id)
);
create table public.kb_documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.kb_organizations(id) on delete cascade,
  project_id uuid,
  kind text not null check(kind in ('CASE','METHODOLOGY','RESEARCH','TEMPLATE')),
  visibility text not null default 'INTERNAL_ONLY' check(visibility in ('INTERNAL_ONLY','CLIENT_SHAREABLE')),
  title text not null,
  source_name text not null,
  storage_path text not null,
  checksum text not null,
  version integer not null default 1 check(version>0),
  state text not null default 'PENDING' check(state in ('PENDING','READY','REVOKED')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique(id,organization_id),
  unique(organization_id,storage_path),
  foreign key (project_id,organization_id) references public.kb_projects(id,organization_id)
);
create table public.kb_document_access (
  document_id uuid not null references public.kb_documents(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  primary key (document_id,user_id)
);
create table public.kb_chunks (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  document_id uuid not null,
  sequence integer not null check(sequence>=0),
  content text not null check(length(content)>0),
  start_offset integer not null check(start_offset>=0),
  end_offset integer not null check(end_offset>start_offset),
  embedding vector(1536),
  created_at timestamptz not null default now(),
  unique(document_id,sequence),
  foreign key (document_id,organization_id) references public.kb_documents(id,organization_id) on delete cascade
);
create index kb_chunks_doc_idx on public.kb_chunks(document_id);
create index kb_chunks_search_idx on public.kb_chunks using gin (to_tsvector('simple', content));

-- No public/anon direct writes or reads. Authenticated reads require
-- organizational membership and explicit document grant.
alter table public.kb_organizations enable row level security;
alter table public.kb_memberships enable row level security;
alter table public.kb_projects enable row level security;
alter table public.kb_documents enable row level security;
alter table public.kb_document_access enable row level security;
alter table public.kb_chunks enable row level security;

create policy kb_membership_self on public.kb_memberships for select to authenticated
  using (user_id = (select auth.uid()));
create policy kb_org_read on public.kb_organizations for select to authenticated
  using (exists (select 1 from public.kb_memberships m
    where m.organization_id = id and m.user_id = (select auth.uid())));
create policy kb_project_read on public.kb_projects for select to authenticated
  using (exists (select 1 from public.kb_memberships m
    where m.organization_id = kb_projects.organization_id and m.user_id = (select auth.uid())));
create policy kb_access_self on public.kb_document_access for select to authenticated
  using (user_id = (select auth.uid()));
create policy kb_doc_read on public.kb_documents for select to authenticated
  using (
    state='READY'
    and exists (select 1 from public.kb_memberships m where m.organization_id=kb_documents.organization_id and m.user_id=(select auth.uid()))
    and exists (select 1 from public.kb_document_access a where a.document_id=kb_documents.id and a.user_id=(select auth.uid()))
  );
create policy kb_chunk_read on public.kb_chunks for select to authenticated
  using (exists (select 1 from public.kb_documents d where d.id=kb_chunks.document_id and d.organization_id=kb_chunks.organization_id));
-- Deliberately NO public client write policies. Ingestion must be performed by
-- an authenticated, authorization-checking backend, not directly from browsers.
-- The storage bucket will be created PRIVATE via a separate provisioning step;
-- never expose it through an unauthenticated public upload endpoint.
