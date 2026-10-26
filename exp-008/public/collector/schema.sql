CREATE TABLE IF NOT EXISTS exp008_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experiment TEXT NOT NULL CHECK (experiment = 'EXP-008'),
  variant TEXT NOT NULL CHECK (variant IN ('CONTROL','TREATMENT')),
  session_id TEXT NOT NULL,
  event_name TEXT NOT NULL CHECK (
    event_name IN (
      'page_view',
      'engaged_5s',
      'engaged_15s',
      'acquisition_details_click',
      'collector_intent_confirm',
      'collector_intent_decline'
    )
  ),
  client_ts TEXT,
  received_at TEXT NOT NULL,
  UNIQUE (experiment, variant, session_id, event_name)
);

CREATE INDEX IF NOT EXISTS idx_exp008_variant
  ON exp008_events (variant);

CREATE INDEX IF NOT EXISTS idx_exp008_event
  ON exp008_events (event_name);

CREATE INDEX IF NOT EXISTS idx_exp008_received
  ON exp008_events (received_at);
