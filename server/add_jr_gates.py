#!/usr/bin/env python3
"""
JR線の駅にゲートを追加するスクリプト

各駅に入口（IN）と出口（OUT）のゲートを追加
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "felica_gate.db"

def add_gates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 全駅を取得（既存の3駅を除く）
    cursor.execute("SELECT id, code, name FROM stations WHERE code LIKE 'J%'")
    stations = cursor.fetchall()

    added_count = 0
    skipped_count = 0

    for station_id, station_code, station_name in stations:
        # 各駅に入口と出口のゲートを追加
        gates = [
            {"code": f"{station_code}_IN", "name": f"{station_name} 入口"},
            {"code": f"{station_code}_OUT", "name": f"{station_name} 出口"},
        ]

        for gate in gates:
            try:
                # 既存チェック
                cursor.execute("SELECT id FROM gates WHERE code = ?", (gate["code"],))
                existing = cursor.fetchone()

                if existing:
                    skipped_count += 1
                    continue

                # ゲートを追加
                cursor.execute(
                    "INSERT INTO gates (code, station_id, name) VALUES (?, ?, ?)",
                    (gate["code"], station_id, gate["name"])
                )
                added_count += 1

            except sqlite3.IntegrityError as e:
                print(f"✗ エラー: {gate['name']} ({gate['code']}) - {e}")
                skipped_count += 1

    conn.commit()
    conn.close()

    print(f"{'='*60}")
    print(f"✅ 完了: {added_count}ゲートを追加しました")
    print(f"⚠ スキップ: {skipped_count}ゲート")
    print(f"{'='*60}")

    # 追加後のゲート数を表示
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gates")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"\n現在のゲート数: {total}個")

if __name__ == "__main__":
    print("JR線の駅にゲートを追加します...\n")
    add_gates()
