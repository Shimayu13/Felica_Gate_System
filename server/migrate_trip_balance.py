#!/usr/bin/env python3
"""
トリップテーブルに残高履歴フィールドを追加するマイグレーションスクリプト
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "felica_gate.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # fare_amountカラムを追加
    try:
        cursor.execute("ALTER TABLE trips ADD COLUMN fare_amount REAL")
        print("✓ trips.fare_amount カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ trips.fare_amount カラムは既に存在します")
        else:
            raise

    # balance_beforeカラムを追加
    try:
        cursor.execute("ALTER TABLE trips ADD COLUMN balance_before REAL")
        print("✓ trips.balance_before カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ trips.balance_before カラムは既に存在します")
        else:
            raise

    # balance_afterカラムを追加
    try:
        cursor.execute("ALTER TABLE trips ADD COLUMN balance_after REAL")
        print("✓ trips.balance_after カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ trips.balance_after カラムは既に存在します")
        else:
            raise

    conn.commit()
    conn.close()
    print("\n✅ マイグレーション完了")

if __name__ == "__main__":
    migrate()
