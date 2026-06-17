-- ============================================================
-- Rio 2027 Birthday Site — Supabase Schema
-- Run this in the Supabase SQL editor after creating your project
-- ============================================================

-- Guests table (codes + names — NOT readable by anon key)
create table if not exists guests (
  code text primary key,
  name text not null,
  active boolean default true,
  is_admin boolean default false,
  created_at timestamptz default now()
);

-- RSVPs
create table if not exists rsvps (
  id uuid primary key default gen_random_uuid(),
  guest_code text references guests(code),
  name text,
  attending text,
  hotel text,
  dietary text,
  notes text,
  trip_tier text,
  created_at timestamptz default now(),
  unique (guest_code)
);

-- Offerings
create table if not exists offerings (
  id uuid primary key default gen_random_uuid(),
  guest_code text references guests(code),
  guest_name text,
  offering_type text not null,
  x_position numeric,
  y_position numeric,
  rotation numeric,
  scale numeric,
  created_at timestamptz default now()
);

-- Stays
create table if not exists stays (
  id uuid primary key default gen_random_uuid(),
  guest_code text references guests(code),
  name text,
  hotel text,
  arrive date,
  depart date,
  created_at timestamptz default now(),
  unique (guest_code)
);

-- Costume photos
create table if not exists costume_photos (
  id uuid primary key default gen_random_uuid(),
  guest_code text references guests(code),
  name text,
  image_url text not null,
  created_at timestamptz default now()
);

-- ============================================================
-- Row Level Security
-- The anon key CANNOT read guests (codes stay server-side only).
-- ============================================================

alter table guests enable row level security;
alter table rsvps enable row level security;
alter table offerings enable row level security;
alter table stays enable row level security;
alter table costume_photos enable row level security;

-- guests: no public access at all (admin only via service role)
create policy "No public read on guests" on guests for select using (false);
create policy "No public write on guests" on guests for insert with check (false);

-- rsvps: anyone can insert their own; no public select (admin reads via service role)
create policy "Insert own rsvp" on rsvps for insert with check (true);
create policy "Select own rsvp" on rsvps for select using (true);

-- offerings: public can insert and select (shared altar)
create policy "Insert offerings" on offerings for insert with check (true);
create policy "Select offerings" on offerings for select using (true);

-- stays: public can insert and select (shared Who's Where)
create policy "Insert stays" on stays for insert with check (true);
create policy "Select stays" on stays for select using (true);

-- costume_photos: public can insert and select
create policy "Insert costume photos" on costume_photos for insert with check (true);
create policy "Select costume photos" on costume_photos for select using (true);

-- ============================================================
-- Storage bucket for costume photos
-- Create this in Supabase Dashboard → Storage:
--   Bucket name: costume-photos
--   Public: yes (so image URLs work without auth)
-- ============================================================

-- ============================================================
-- Ben's guest code + initial seed
-- ============================================================
insert into guests (code, name, active, is_admin) values
  ('BEN-HOST', 'Ben', true, true)
on conflict (code) do update set is_admin = true;

-- If upgrading an existing database, run these migrations:
-- alter table guests add column if not exists is_admin boolean default false;
-- update guests set is_admin = true where code = 'BEN-HOST';
-- alter table rsvps add column if not exists trip_tier text;

-- Add more guests here or use the /admin panel:
-- insert into guests (code, name, active) values ('BEN-DALTON', 'Dalton', true);
-- insert into guests (code, name, active) values ('BEN-MARCUS', 'Marcus', true);
