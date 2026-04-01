begin;

create table if not exists public.certificates (
  id bigint generated always as identity primary key,
  id_alumno text not null,
  id_curso bigint not null references public.courses(id) on delete cascade,
  id_certificacion text not null,
  fecha_emision timestamptz not null default timezone('utc', now()),
  constraint uq_certificates_id_certificacion unique (id_certificacion),
  constraint uq_certificates_alumno_curso unique (id_alumno, id_curso)
);

create index if not exists idx_certificates_lookup
  on public.certificates (id_curso, id_alumno);

commit;
