create table if not exists sinais_ia (
    id          bigint generated always as identity primary key,
    empresa_id  bigint references empresas(id) not null,
    camada      text not null check (camada in ('institucional','imprensa','linkedin_vagas','linkedin_posts','gupy_vagas')),
    encontrado  boolean not null default false,
    evidencia   text,
    fonte_url   text,
    checado_em  timestamptz default now()
  );