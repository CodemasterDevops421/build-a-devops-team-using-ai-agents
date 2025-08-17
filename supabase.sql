-- supabase.sql

create table if not exists ci_pipelines (
  id bigint generated always as identity primary key,
  created_at timestamp with time zone default now(),
  workflow_name text not null,
  python_version text not null,
  run_tests boolean not null,
  groq_api_endpoint text not null,
  groq_api_key text not null,
  pipeline_yaml text not null
);

create table if not exists dockerfiles (
  id bigint generated always as identity primary key,
  created_at timestamp with time zone default now(),
  base_image text not null,
  expose_port integer not null,
  copy_source text not null,
  work_dir text not null,
  groq_api_endpoint text not null,
  groq_api_key text not null,
  dockerfile_content text not null
);

create table if not exists build_predictions (
  id bigint generated always as identity primary key,
  created_at timestamp with time zone default now(),
  model text not null,
  groq_api_key text not null,
  build_id text not null,
  commit_hash text not null,
  files_changed text[] not null,
  tests_failed boolean not null,
  coverage double precision not null,
  prediction jsonb not null
);

create table if not exists build_status (
  id bigint generated always as identity primary key,
  created_at timestamp with time zone default now(),
  image_tag text not null,
  status text not null
);
