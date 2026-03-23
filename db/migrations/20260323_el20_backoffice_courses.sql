begin;

alter table public.courses
  add column if not exists published boolean not null default true;

create table if not exists public.classes (
  id bigint generated always as identity primary key,
  id_curso bigint not null references public.courses(id) on delete cascade,
  nombre_clase text not null,
  descripcion text not null default '',
  url_video text not null default ''
);

create table if not exists public.course_student (
  id bigint generated always as identity primary key,
  id_alumno text not null,
  id_curso bigint not null references public.courses(id) on delete cascade,
  status boolean not null default false,
  id_certificado text,
  fecha_asignacion timestamptz not null default timezone('utc', now()),
  fecha_finalizado timestamptz,
  constraint uq_course_student_alumno_curso unique (id_alumno, id_curso)
);

create table if not exists public.classes_student (
  id bigint generated always as identity primary key,
  id_curso bigint not null references public.courses(id) on delete cascade,
  id_clase bigint not null references public.classes(id) on delete cascade,
  id_alumno text not null,
  time integer not null default 0,
  status boolean not null default false,
  constraint uq_classes_student_curso_clase_alumno unique (id_curso, id_clase, id_alumno)
);

create index if not exists idx_classes_id_curso
  on public.classes (id_curso);

create index if not exists idx_course_student_lookup
  on public.course_student (id_curso, id_alumno);

create index if not exists idx_classes_student_lookup
  on public.classes_student (id_curso, id_alumno, status);

commit;
