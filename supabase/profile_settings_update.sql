-- Atualizacao especifica para Perfil / Nome de usuario
-- Rode no Supabase SQL Editor se aparecer:
-- "O banco ainda precisa da atualizacao de perfil"

alter table public.profiles add column if not exists username text;
alter table public.profiles add column if not exists avatar_id integer not null default 1;

create unique index if not exists profiles_username_lower_idx
on public.profiles (lower(username))
where username is not null;

update public.profiles
set
  username = coalesce(username, lower(regexp_replace(split_part(email, '@', 1), '[^a-zA-Z0-9_]', '', 'g'))),
  display_name = coalesce(username, display_name)
where username is null;
