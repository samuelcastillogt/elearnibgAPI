begin;

create table if not exists public.categories (
  id bigint generated always as identity primary key,
  name text unique not null,
  created_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists idx_categories_name_unique
  on public.categories (name);

insert into public.categories (name)
values
  ('Frontend'),
  ('Backend'),
  ('Diseno')
on conflict (name) do nothing;

insert into public.categories (name)
select distinct c.category
from public.courses c
where c.category is not null
  and btrim(c.category) <> ''
on conflict (name) do nothing;

commit;
