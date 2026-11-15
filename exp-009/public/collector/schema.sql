CREATE TABLE IF NOT EXISTS exp009_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experiment TEXT NOT NULL CHECK (experiment = 'EXP-009'),
  variant TEXT NOT NULL CHECK (variant IN ('CONTROL','TREATMENT')),
  session_id TEXT NOT NULL,
  event_name TEXT NOT NULL CHECK (
    event_name IN ('landing_page_view','engaged_5s','engaged_15s','artwork_open')
  ),
  source TEXT NOT NULL CHECK (source = 'moltbook_exp009'),
  client_ts TEXT,
  received_at TEXT NOT NULL,
  UNIQUE (experiment, variant, session_id, event_name)
);

CREATE TABLE IF NOT EXISTS exp009_control (
  experiment TEXT PRIMARY KEY CHECK (experiment = 'EXP-009'),
  status TEXT NOT NULL CHECK (status IN ('PRELAUNCH','RUNNING','CLOSED')),
  launch_utc TEXT,
  maximum_end_utc TEXT,
  updated_at TEXT NOT NULL
);

INSERT OR IGNORE INTO exp009_control
  (experiment, status, launch_utc, maximum_end_utc, updated_at)
VALUES
  ('EXP-009','PRELAUNCH',NULL,NULL,datetime('now'));

CREATE INDEX IF NOT EXISTS idx_exp009_variant ON exp009_events (variant);
CREATE INDEX IF NOT EXISTS idx_exp009_event ON exp009_events (event_name);
CREATE INDEX IF NOT EXISTS idx_exp009_received ON exp009_events (received_at);
