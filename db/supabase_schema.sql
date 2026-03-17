create table if not exists public.courses (
  id bigint generated always as identity primary key,
  slug text unique not null,
  title text not null,
  category text not null,
  progress integer not null default 0,
  created_at timestamptz not null default timezone('utc', now())
);

insert into public.courses (slug, title, category, progress)
values
  ('react-desde-cero', 'React desde Cero', 'Frontend', 42),
  ('fastapi-para-apis', 'FastAPI para APIs', 'Backend', 65),
  ('fundamentos-ux', 'Fundamentos de UX', 'Diseno', 28)
on conflict (slug) do update set
  title = excluded.title,
  category = excluded.category,
  progress = excluded.progress;
