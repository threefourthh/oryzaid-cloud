-- Enable UUID generator
create extension if not exists "uuid-ossp";

---------------------------------------------------
-- MISSIONS TABLE
---------------------------------------------------

create table if not exists missions (
  id uuid primary key default uuid_generate_v4(),

  mission_id text not null unique,
  mission_name text,

  field_location text,
  area_covered_ha numeric(10,2),
  flight_altitude_m numeric(10,2),

  drone_id text,
  operator_name text,

  center_lat double precision,
  center_lng double precision,

  flight_path jsonb default '[]'::jsonb,
  field_boundary jsonb default '[]'::jsonb,

  capture_time timestamptz default now(),
  started_at timestamptz default now(),

  -- Live telemetry / monitor fields
  flight_status text default 'planned',

  latitude double precision,
  longitude double precision,

  -- GPS / global altitude
  altitude_m double precision,

  -- height above takeoff
  relative_alt_m double precision,

  -- live speed
  speed_mps double precision,

  armed boolean,
  mode text,
  connected boolean,
  source text,

  voltage double precision,
  battery_pct double precision,
  link text,

  updated_at timestamptz default now(),
  created_at timestamptz default now()
);

---------------------------------------------------
-- DETECTIONS TABLE
---------------------------------------------------

create table if not exists detections (
  id uuid primary key default uuid_generate_v4(),

  mission_id text not null,

  class_name text not null,
  class_group text,
  normalized_label text,

  confidence double precision,
  severity_level text,
  affected_area_percent double precision,

  latitude double precision,
  longitude double precision,
  altitude_m double precision,

  heatmap_url text,
  image_url text,

  detected_at timestamptz default now(),
  created_at timestamptz default now()
);

---------------------------------------------------
-- INDEXES
---------------------------------------------------

create index if not exists idx_missions_mission_id
on missions(mission_id);

create index if not exists idx_missions_updated_at
on missions(updated_at);

create index if not exists idx_missions_flight_status
on missions(flight_status);

create index if not exists idx_detections_mission_id
on detections(mission_id);

create index if not exists idx_detections_class_group
on detections(class_group);

create index if not exists idx_detections_detected_at
on detections(detected_at);