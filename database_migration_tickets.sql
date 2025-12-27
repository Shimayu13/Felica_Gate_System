-- 切符システム用データベースマイグレーション
-- 実行日: 2025-12-27

-- ========================================
-- 1. tickets テーブルの作成
-- ========================================

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    qr_token TEXT UNIQUE NOT NULL,
    origin_station TEXT NOT NULL,
    destination_station TEXT NOT NULL,
    ticket_type TEXT NOT NULL,  -- 'single', 'round_trip', 'day_pass'
    price INTEGER NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'used', 'expired', 'cancelled'
    valid_until TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    created_by TEXT,  -- 発券した駅員のID
    notes TEXT
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_tickets_qr_token ON tickets(qr_token);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);

-- ========================================
-- 2. ticket_usage テーブルの作成（使用ログ）
-- ========================================

CREATE TABLE IF NOT EXISTS ticket_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    qr_token TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'entry', 'exit'
    station_code TEXT NOT NULL,
    gate_code TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_ticket_usage_qr_token ON ticket_usage(qr_token);
CREATE INDEX IF NOT EXISTS idx_ticket_usage_ticket_id ON ticket_usage(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_usage_timestamp ON ticket_usage(timestamp);

-- ========================================
-- 3. テストデータの挿入（開発環境用）
-- ========================================

-- 片道切符のサンプル
INSERT OR IGNORE INTO tickets (
    ticket_id, qr_token, origin_station, destination_station,
    ticket_type, price, status, valid_until, created_by, notes
) VALUES (
    'TKT20251227120000AAA',
    'TICKET_QR_sample001_test_single',
    'STATION_1',
    'STATION_2',
    'single',
    200,
    'active',
    datetime('now', '+24 hours'),
    'STAFF001',
    'テスト用片道切符'
);

-- 往復切符のサンプル
INSERT OR IGNORE INTO tickets (
    ticket_id, qr_token, origin_station, destination_station,
    ticket_type, price, status, valid_until, created_by, notes
) VALUES (
    'TKT20251227120001BBB',
    'TICKET_QR_sample002_test_roundtrip',
    'STATION_1',
    'STATION_3',
    'round_trip',
    600,
    'active',
    datetime('now', '+24 hours'),
    'STAFF001',
    'テスト用往復切符'
);

-- 一日券のサンプル
INSERT OR IGNORE INTO tickets (
    ticket_id, qr_token, origin_station, destination_station,
    ticket_type, price, status, valid_until, created_by, notes
) VALUES (
    'TKT20251227120002CCC',
    'TICKET_QR_sample003_test_daypass',
    'STATION_1',
    'STATION_5',
    'day_pass',
    1000,
    'active',
    datetime('now', 'start of day', '+1 day', '-1 second'),
    'STAFF002',
    'テスト用一日券'
);

-- ========================================
-- 4. 既存gate_logsテーブルへの変更（オプション）
-- ========================================

-- gate_logsテーブルに切符関連のカラムを追加する場合
-- ALTER TABLE gate_logs ADD COLUMN ticket_id TEXT;

-- ========================================
-- 5. ビューの作成（便利な集計用）
-- ========================================

-- 有効な切符の一覧
CREATE VIEW IF NOT EXISTS active_tickets AS
SELECT
    ticket_id,
    qr_token,
    origin_station,
    destination_station,
    ticket_type,
    price,
    status,
    valid_until,
    created_at,
    created_by
FROM tickets
WHERE status = 'active'
  AND valid_until > datetime('now');

-- 今日発券された切符
CREATE VIEW IF NOT EXISTS todays_tickets AS
SELECT
    ticket_id,
    qr_token,
    origin_station,
    destination_station,
    ticket_type,
    price,
    status,
    created_at,
    created_by
FROM tickets
WHERE date(created_at) = date('now');

-- 切符の使用状況統計
CREATE VIEW IF NOT EXISTS ticket_stats AS
SELECT
    date(created_at) as date,
    ticket_type,
    status,
    COUNT(*) as count,
    SUM(price) as total_revenue
FROM tickets
GROUP BY date(created_at), ticket_type, status
ORDER BY created_at DESC;

-- ========================================
-- 6. トリガーの作成（自動有効期限チェック）
-- ========================================

-- 有効期限切れ切符を自動的にexpiredにする（実際の運用では定期バッチ処理を推奨）
-- CREATE TRIGGER IF NOT EXISTS auto_expire_tickets
-- AFTER SELECT ON tickets
-- BEGIN
--     UPDATE tickets
--     SET status = 'expired'
--     WHERE status = 'active'
--       AND valid_until < datetime('now');
-- END;

-- ========================================
-- マイグレーション完了
-- ========================================

SELECT 'Ticket system migration completed successfully' as message;

-- 確認クエリ
SELECT
    'Tickets table:' as check_name,
    COUNT(*) as record_count
FROM tickets
UNION ALL
SELECT
    'Ticket usage table:',
    COUNT(*)
FROM ticket_usage;
