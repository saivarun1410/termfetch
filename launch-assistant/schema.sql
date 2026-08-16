CREATE TABLE IF NOT EXISTS push_subscriptions (
  endpoint TEXT PRIMARY KEY,
  expiration_time INTEGER,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_test_at TEXT
);

CREATE TABLE IF NOT EXISTS sent_notifications (
  post_id TEXT PRIMARY KEY,
  sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  recipient_count INTEGER NOT NULL DEFAULT 0
);
