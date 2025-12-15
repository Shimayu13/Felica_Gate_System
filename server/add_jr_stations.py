#!/usr/bin/env python3
"""
JR線の駅データを追加するスクリプト

- 京浜東北線: 東京〜大船
- 横須賀線: 品川〜大船
- 南武線: 武蔵小杉〜川崎
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "felica_gate.db"

# 駅データ
STATIONS = [
    # 京浜東北線（東京〜大船）
    {"code": "JK01", "name": "東京"},
    {"code": "JK02", "name": "有楽町"},
    {"code": "JK03", "name": "新橋"},
    {"code": "JK04", "name": "浜松町"},
    {"code": "JK05", "name": "田町"},
    {"code": "JK06", "name": "高輪ゲートウェイ"},
    {"code": "JK07", "name": "品川"},
    {"code": "JK08", "name": "大井町"},
    {"code": "JK09", "name": "大森"},
    {"code": "JK10", "name": "蒲田"},
    {"code": "JK11", "name": "川崎"},
    {"code": "JK12", "name": "鶴見"},
    {"code": "JK13", "name": "新子安"},
    {"code": "JK14", "name": "東神奈川"},
    {"code": "JK15", "name": "横浜"},
    {"code": "JK16", "name": "桜木町"},
    {"code": "JK17", "name": "関内"},
    {"code": "JK18", "name": "石川町"},
    {"code": "JK19", "name": "山手"},
    {"code": "JK20", "name": "根岸"},
    {"code": "JK21", "name": "磯子"},
    {"code": "JK22", "name": "新杉田"},
    {"code": "JK23", "name": "洋光台"},
    {"code": "JK24", "name": "港南台"},
    {"code": "JK25", "name": "本郷台"},
    {"code": "JK26", "name": "大船"},

    # 横須賀線（品川〜大船）
    {"code": "JO01", "name": "品川"},
    {"code": "JO02", "name": "西大井"},
    {"code": "JO03", "name": "武蔵小杉"},
    {"code": "JO04", "name": "新川崎"},
    {"code": "JO05", "name": "横浜"},
    {"code": "JO06", "name": "保土ケ谷"},
    {"code": "JO07", "name": "東戸塚"},
    {"code": "JO08", "name": "戸塚"},
    {"code": "JO09", "name": "大船"},

    # 南武線（武蔵小杉〜川崎）
    {"code": "JN01", "name": "武蔵小杉"},
    {"code": "JN02", "name": "武蔵中原"},
    {"code": "JN03", "name": "武蔵新城"},
    {"code": "JN04", "name": "武蔵溝ノ口"},
    {"code": "JN05", "name": "津田山"},
    {"code": "JN06", "name": "久地"},
    {"code": "JN07", "name": "宿河原"},
    {"code": "JN08", "name": "登戸"},
    {"code": "JN09", "name": "中野島"},
    {"code": "JN10", "name": "稲田堤"},
    {"code": "JN11", "name": "矢野口"},
    {"code": "JN12", "name": "稲城長沼"},
    {"code": "JN13", "name": "南多摩"},
    {"code": "JN14", "name": "府中本町"},
    {"code": "JN15", "name": "分倍河原"},
    {"code": "JN16", "name": "谷保"},
    {"code": "JN17", "name": "矢川"},
    {"code": "JN18", "name": "西国立"},
    {"code": "JN19", "name": "立川"},
    {"code": "JN20", "name": "川崎"},  # 南武線の川崎側端点
]

def add_stations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    added_count = 0
    skipped_count = 0

    for station in STATIONS:
        try:
            # 既存チェック
            cursor.execute("SELECT id FROM stations WHERE code = ?", (station["code"],))
            existing = cursor.fetchone()

            if existing:
                print(f"⚠ スキップ: {station['name']} ({station['code']}) - 既に存在します")
                skipped_count += 1
                continue

            # 駅を追加
            cursor.execute(
                "INSERT INTO stations (code, name) VALUES (?, ?)",
                (station["code"], station["name"])
            )
            print(f"✓ 追加: {station['name']} ({station['code']})")
            added_count += 1

        except sqlite3.IntegrityError as e:
            print(f"✗ エラー: {station['name']} ({station['code']}) - {e}")
            skipped_count += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"✅ 完了: {added_count}駅を追加しました")
    print(f"⚠ スキップ: {skipped_count}駅")
    print(f"{'='*60}")

    # 追加後の駅数を表示
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stations")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"\n現在の駅数: {total}駅")

if __name__ == "__main__":
    print("JR線の駅データを追加します...\n")
    add_stations()
