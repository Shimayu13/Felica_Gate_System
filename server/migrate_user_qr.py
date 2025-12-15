#!/usr/bin/env python3
"""
ユーザーテーブルにqr_tokenとcard_idmカラムを追加するマイグレーションスクリプト
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "felica_gate.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # usersテーブルにqr_tokenカラムを追加（SQLiteはALTER TABLEでUNIQUE制約を追加できないため、まずカラムのみ追加）
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN qr_token TEXT")
        print("✓ users.qr_token カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ users.qr_token カラムは既に存在します")
        else:
            raise

    # usersテーブルにcard_idmカラムを追加
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN card_idm TEXT")
        print("✓ users.card_idm カラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ users.card_idm カラムは既に存在します")
        else:
            raise

    # qr_tokenにUNIQUEインデックスを作成（UNIQUE制約の代わり）
    try:
        cursor.execute("CREATE UNIQUE INDEX idx_users_qr_token ON users(qr_token)")
        print("✓ users.qr_token UNIQUEインデックスを作成しました")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("⚠ users.qr_token インデックスは既に存在します")
        else:
            raise

    # 既存のユーザーのqr_tokenをcardsテーブルから取得して設定
    cursor.execute("""
        UPDATE users
        SET qr_token = (
            SELECT qr_token
            FROM cards
            WHERE cards.user_id = users.id
            AND cards.qr_token IS NOT NULL
            LIMIT 1
        )
        WHERE qr_token IS NULL
    """)
    updated = cursor.rowcount
    if updated > 0:
        print(f"✓ {updated}件のユーザーにQRトークンを設定しました")

    # 既存のユーザーのcard_idmをcardsテーブルから取得して設定
    cursor.execute("""
        UPDATE users
        SET card_idm = (
            SELECT idm
            FROM cards
            WHERE cards.user_id = users.id
            AND cards.idm IS NOT NULL
            LIMIT 1
        )
        WHERE card_idm IS NULL
    """)
    updated = cursor.rowcount
    if updated > 0:
        print(f"✓ {updated}件のユーザーにカードIDmを設定しました")

    conn.commit()
    conn.close()
    print("\n✅ マイグレーション完了")

if __name__ == "__main__":
    migrate()
