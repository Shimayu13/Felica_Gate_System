#!/usr/bin/env python3
"""
定期券テーブルを追加するマイグレーションスクリプト
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "felica_gate.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # passesテーブルを作成
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pass_type TEXT NOT NULL,
                station_from TEXT NOT NULL,
                station_to TEXT NOT NULL,
                valid_from TIMESTAMP NOT NULL,
                valid_until TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✓ passesテーブルを作成しました")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ passesテーブルは既に存在します")
        else:
            raise

    # tripsテーブルにused_pass_idカラムを追加
    try:
        cursor.execute("ALTER TABLE trips ADD COLUMN used_pass_id INTEGER")
        print("✓ trips.used_pass_id カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ trips.used_pass_id カラムは既に存在します")
        else:
            raise

    # used_pass_idに外部キー制約を追加するためのインデックス作成
    try:
        cursor.execute("CREATE INDEX idx_trips_used_pass_id ON trips(used_pass_id)")
        print("✓ trips.used_pass_id インデックスを作成しました")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ trips.used_pass_id インデックスは既に存在します")
        else:
            raise

    # passesテーブルにインデックスを作成
    try:
        cursor.execute("CREATE INDEX idx_passes_user_id ON passes(user_id)")
        print("✓ passes.user_id インデックスを作成しました")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ passes.user_id インデックスは既に存在します")
        else:
            raise

    try:
        cursor.execute("CREATE INDEX idx_passes_valid_dates ON passes(valid_from, valid_until)")
        print("✓ passes有効期間インデックスを作成しました")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ passes有効期間インデックスは既に存在します")
        else:
            raise

    conn.commit()
    conn.close()
    print("\n✅ マイグレーション完了")

if __name__ == "__main__":
    migrate()
