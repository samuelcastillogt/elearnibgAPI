create table if not exists public.categories (
  id bigint generated always as identity primary key,
  name text unique not null,
  created_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists idx_categories_name_unique
  on public.categories (name);

create table if not exists public.courses (
  id bigint generated always as identity primary key,
  slug text unique not null,
  title text not null,
  category text not null,
  published boolean not null default true,
  progress integer not null default 0,
  created_at timestamptz not null default timezone('utc', now())
);

alter table public.courses
  add column if not exists published boolean not null default true;

insert into public.categories (name)
values
  ('Frontend'),
  ('Backend'),
  ('Diseno')
on conflict (name) do nothing;

insert into public.courses (slug, title, category, published, progress)
values
  ('react-desde-cero', 'React desde Cero', 'Frontend', true, 42),
  ('fastapi-para-apis', 'FastAPI para APIs', 'Backend', true, 65),
  ('fundamentos-ux', 'Fundamentos de UX', 'Diseno', true, 28)
on conflict (slug) do update set
  title = excluded.title,
  category = excluded.category,
  published = excluded.published,
  progress = excluded.progress;

insert into public.categories (name)
select distinct c.category
from public.courses c
where c.category is not null
  and btrim(c.category) <> ''
on conflict (name) do nothing;

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
  unique (id_alumno, id_curso)
);

create table if not exists public.classes_student (
  id bigint generated always as identity primary key,
  id_curso bigint not null references public.courses(id) on delete cascade,
  id_clase bigint not null references public.classes(id) on delete cascade,
  id_alumno text not null,
  time integer not null default 0,
  status boolean not null default false,
  unique (id_curso, id_clase, id_alumno)
);

insert into public.classes (id_curso, nombre_clase, descripcion, url_video)
select c.id,
  v.nombre_clase,
  v.descripcion,
  v.url_video
from public.courses c
join (
  values
    ('react-desde-cero', 'Introduccion a React', 'Setup inicial, JSX y componentes', 'https://example.com/videos/react-1'),
    ('react-desde-cero', 'Estado y eventos', 'useState, eventos y formularios', 'https://example.com/videos/react-2'),
    ('react-desde-cero', 'Routing y proyecto final', 'Navegacion, rutas privadas y deploy', 'https://example.com/videos/react-3'),
    ('fastapi-para-apis', 'Fundamentos de FastAPI', 'Modelos Pydantic y rutas basicas', 'https://example.com/videos/fastapi-1'),
    ('fastapi-para-apis', 'Persistencia y autenticacion', 'CRUD con base de datos y login', 'https://example.com/videos/fastapi-2'),
    ('fastapi-para-apis', 'Deployment y observabilidad', 'Versionado, logs y despliegue', 'https://example.com/videos/fastapi-3'),
    ('fundamentos-ux', 'Principios UX', 'Heuristicas, accesibilidad y consistencia', 'https://example.com/videos/ux-1'),
    ('fundamentos-ux', 'Investigacion de usuarios', 'Personas, entrevistas y mapas de empatia', 'https://example.com/videos/ux-2'),
    ('fundamentos-ux', 'Prototipado y validacion', 'Wireframes, testing y mejoras iterativas', 'https://example.com/videos/ux-3')
) as v(course_slug, nombre_clase, descripcion, url_video)
  on v.course_slug = c.slug
where not exists (
  select 1
  from public.classes existing
  where existing.id_curso = c.id
    and existing.nombre_clase = v.nombre_clase
);
