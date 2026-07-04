-- Album da Copa 2026 - estrutura inicial Supabase
-- Rode este arquivo no Supabase SQL Editor antes de usar login/sincronizacao.
-- A chave publishable pode ficar no HTML; a seguranca fica nas politicas RLS abaixo.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null,
  email text,
  username text,
  avatar_id integer not null default 1,
  last_seen timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles add column if not exists email text;
alter table public.profiles add column if not exists username text;
alter table public.profiles add column if not exists avatar_id integer not null default 1;
alter table public.profiles add column if not exists last_seen timestamptz;
create unique index if not exists profiles_email_lower_idx
on public.profiles (lower(email))
where email is not null;
create unique index if not exists profiles_username_lower_idx
on public.profiles (lower(username))
where username is not null;

create table if not exists public.albums (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{"stickers":{},"notes":""}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.user_stickers (
  user_id uuid not null references auth.users(id) on delete cascade,
  code text not null,
  qty integer not null default 0 check (qty >= 0 and qty <= 99),
  updated_at timestamptz not null default now(),
  primary key (user_id, code)
);

create table if not exists public.trade_offers (
  id uuid primary key default gen_random_uuid(),
  from_user uuid not null references auth.users(id) on delete cascade,
  to_user uuid references auth.users(id) on delete cascade,
  offered_codes text[] not null default '{}',
  requested_codes text[] not null default '{}',
  message text not null default '',
  status text not null default 'open' check (status in ('open','accepted','declined','cancelled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.friendships (
  id uuid primary key default gen_random_uuid(),
  requester uuid not null references auth.users(id) on delete cascade,
  addressee uuid not null references auth.users(id) on delete cascade,
  status text not null default 'pending' check (status in ('pending','accepted','declined','blocked')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint friendships_no_self check (requester <> addressee)
);

create unique index if not exists friendships_pair_idx
on public.friendships (least(requester, addressee), greatest(requester, addressee));

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  sender uuid not null references auth.users(id) on delete cascade,
  receiver uuid not null references auth.users(id) on delete cascade,
  body text not null check (char_length(body) between 1 and 1000),
  read_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.albums enable row level security;
alter table public.user_stickers enable row level security;
alter table public.trade_offers enable row level security;
alter table public.friendships enable row level security;
alter table public.messages enable row level security;

drop policy if exists "profiles_select_authenticated" on public.profiles;
create policy "profiles_select_authenticated"
on public.profiles for select
to authenticated
using (true);

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
on public.profiles for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
on public.profiles for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "albums_select_own" on public.albums;
create policy "albums_select_own"
on public.albums for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "albums_insert_own" on public.albums;
create policy "albums_insert_own"
on public.albums for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "albums_update_own" on public.albums;
create policy "albums_update_own"
on public.albums for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "albums_delete_own" on public.albums;
create policy "albums_delete_own"
on public.albums for delete
to authenticated
using (auth.uid() = user_id);

drop policy if exists "stickers_select_authenticated" on public.user_stickers;
create policy "stickers_select_authenticated"
on public.user_stickers for select
to authenticated
using (true);

drop policy if exists "stickers_insert_own" on public.user_stickers;
create policy "stickers_insert_own"
on public.user_stickers for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "stickers_update_own" on public.user_stickers;
create policy "stickers_update_own"
on public.user_stickers for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "stickers_delete_own" on public.user_stickers;
create policy "stickers_delete_own"
on public.user_stickers for delete
to authenticated
using (auth.uid() = user_id);

drop policy if exists "offers_select_participant" on public.trade_offers;
create policy "offers_select_participant"
on public.trade_offers for select
to authenticated
using (auth.uid() = from_user or auth.uid() = to_user);

drop policy if exists "offers_insert_own" on public.trade_offers;
create policy "offers_insert_own"
on public.trade_offers for insert
to authenticated
with check (auth.uid() = from_user);

drop policy if exists "offers_update_participant" on public.trade_offers;
create policy "offers_update_participant"
on public.trade_offers for update
to authenticated
using (auth.uid() = from_user or auth.uid() = to_user)
with check (auth.uid() = from_user or auth.uid() = to_user);

drop policy if exists "friendships_select_participant" on public.friendships;
create policy "friendships_select_participant"
on public.friendships for select
to authenticated
using (auth.uid() = requester or auth.uid() = addressee);

drop policy if exists "friendships_insert_own" on public.friendships;
create policy "friendships_insert_own"
on public.friendships for insert
to authenticated
with check (auth.uid() = requester);

drop policy if exists "friendships_update_participant" on public.friendships;
create policy "friendships_update_participant"
on public.friendships for update
to authenticated
using (auth.uid() = requester or auth.uid() = addressee)
with check (auth.uid() = requester or auth.uid() = addressee);

drop policy if exists "friendships_delete_participant" on public.friendships;
create policy "friendships_delete_participant"
on public.friendships for delete
to authenticated
using (auth.uid() = requester or auth.uid() = addressee);

drop policy if exists "messages_select_participant" on public.messages;
create policy "messages_select_participant"
on public.messages for select
to authenticated
using (auth.uid() = sender or auth.uid() = receiver);

drop policy if exists "messages_insert_sender" on public.messages;
create policy "messages_insert_sender"
on public.messages for insert
to authenticated
with check (
  auth.uid() = sender
  and exists (
    select 1 from public.friendships f
    where f.status = 'accepted'
      and ((f.requester = sender and f.addressee = receiver) or (f.requester = receiver and f.addressee = sender))
  )
);

drop policy if exists "messages_update_receiver" on public.messages;
create policy "messages_update_receiver"
on public.messages for update
to authenticated
using (auth.uid() = receiver)
with check (auth.uid() = receiver);
