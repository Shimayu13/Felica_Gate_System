#!/usr/bin/env python3
"""
CSVデータに基づいて駅データを完全に再構築するスクリプト

実行内容:
1. 既存の駅データとゲートデータをすべて削除
2. CSVから駅情報を抽出してstationsテーブルに追加
3. 各駅にゲートを自動生成（入口・出口）
4. station_routesテーブルに営業距離データを追加
5. fare_tableテーブルに運賃データを追加
"""

import sqlite3
import csv
import sys
from collections import OrderedDict

DB_PATH = 'felica_gate.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== 駅データの完全再構築 ===\n")

    # ステップ1: 既存データの削除
    print("[1/5] 既存データを削除中...")
    cursor.execute("DELETE FROM trips")
    cursor.execute("DELETE FROM passes")
    cursor.execute("DELETE FROM gates")
    cursor.execute("DELETE FROM station_routes")
    cursor.execute("DELETE FROM stations")
    cursor.execute("DELETE FROM fare_table")
    conn.commit()
    print("  ✓ 既存データを削除しました")

    # ステップ2: CSVから駅情報を抽出
    print("\n[2/5] CSVから駅情報を抽出中...")
    try:
        with open('営業距離データ.csv', 'r', encoding='shift_jis') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ

            # 駅情報を格納（ID順、重複削除）
            stations_dict = OrderedDict()
            routes_data = []

            for row in reader:
                if not row[0]:
                    continue

                station_id = int(row[0])
                station_name = row[1]
                distance = float(row[2])
                line = row[3]
                sub_line = row[4]

                # 駅情報を保存（最初に出現したものを使用）
                if station_id not in stations_dict:
                    stations_dict[station_id] = station_name

                # ルート情報を保存
                routes_data.append({
                    'station_id': station_id,
                    'line': line,
                    'sub_line': sub_line,
                    'distance': distance
                })

        print(f"  ✓ {len(stations_dict)}駅を抽出しました")
        print(f"  ✓ {len(routes_data)}件のルート情報を抽出しました")

    except FileNotFoundError:
        print("  エラー: 営業距離データ.csv が見つかりません")
        conn.close()
        sys.exit(1)

    # ステップ3: 駅をstationsテーブルに追加
    print("\n[3/5] 駅をデータベースに追加中...")
    station_code_map = {}  # IDからコードへのマッピング

    for station_id, station_name in stations_dict.items():
        # 駅コードを生成（STATIONのIDをそのまま使用）
        station_code = f"STATION_{station_id}"

        cursor.execute("""
            INSERT INTO stations (id, code, name)
            VALUES (?, ?, ?)
        """, (station_id, station_code, station_name))

        station_code_map[station_id] = station_code

    conn.commit()
    print(f"  ✓ {len(stations_dict)}駅を追加しました")

    # ステップ4: 各駅にゲートを自動生成
    print("\n[4/5] 各駅にゲートを生成中...")
    gate_count = 0
    for station_id, station_name in stations_dict.items():
        # 入口ゲート
        cursor.execute("""
            INSERT INTO gates (code, station_id, name)
            VALUES (?, ?, ?)
        """, (f"STATION_{station_id}_IN", station_id, f"{station_name} 入口"))
        gate_count += 1

        # 出口ゲート
        cursor.execute("""
            INSERT INTO gates (code, station_id, name)
            VALUES (?, ?, ?)
        """, (f"STATION_{station_id}_OUT", station_id, f"{station_name} 出口"))
        gate_count += 1

    conn.commit()
    print(f"  ✓ {gate_count}個のゲートを生成しました（各駅2個）")

    # ステップ5: station_routesにルート情報を追加
    print("\n[5/5] ルート情報を追加中...")

    # station_routesテーブルを作成（存在しない場合）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS station_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER NOT NULL,
            line TEXT NOT NULL,
            sub_line TEXT NOT NULL,
            distance_from_origin REAL NOT NULL,
            FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
            UNIQUE(station_id, line, sub_line)
        )
    """)

    route_count = 0
    for route in routes_data:
        cursor.execute("""
            INSERT OR IGNORE INTO station_routes
            (station_id, line, sub_line, distance_from_origin)
            VALUES (?, ?, ?, ?)
        """, (route['station_id'], route['line'], route['sub_line'], route['distance']))
        if cursor.rowcount > 0:
            route_count += 1

    conn.commit()
    print(f"  ✓ {route_count}件のルート情報を追加しました")

    # 運賃テーブルをインポート
    print("\n運賃テーブルをインポート中...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fare_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            min_distance_km REAL NOT NULL UNIQUE,
            fare INTEGER NOT NULL
        )
    """)

    try:
        with open('運賃体系.csv', 'r', encoding='shift_jis') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ

            fare_count = 0
            for row in reader:
                if not row[0] or not row[1]:
                    continue

                min_distance = float(row[0])
                fare = int(row[1])

                cursor.execute("""
                    INSERT OR REPLACE INTO fare_table (min_distance_km, fare)
                    VALUES (?, ?)
                """, (min_distance, fare))
                fare_count += 1

        conn.commit()
        print(f"  ✓ {fare_count}件の運賃データをインポートしました")

    except FileNotFoundError:
        print("  エラー: 運賃体系.csv が見つかりません")

    # 確認情報を表示
    print("\n=== 再構築完了 ===")
    print("\n現在のデータベース状態:")

    cursor.execute("SELECT COUNT(*) FROM stations")
    station_count = cursor.fetchone()[0]
    print(f"  駅数: {station_count}")

    cursor.execute("SELECT COUNT(*) FROM gates")
    gate_count = cursor.fetchone()[0]
    print(f"  ゲート数: {gate_count}")

    cursor.execute("SELECT COUNT(*) FROM station_routes")
    route_count = cursor.fetchone()[0]
    print(f"  ルート数: {route_count}")

    cursor.execute("SELECT COUNT(*) FROM fare_table")
    fare_count = cursor.fetchone()[0]
    print(f"  運賃テーブル: {fare_count}段階")

    # サンプルデータを表示
    print("\n駅ルート情報（サンプル: 東京駅 ID=1）:")
    cursor.execute("""
        SELECT s.id, s.name, s.code, sr.line, sr.sub_line, sr.distance_from_origin
        FROM stations s
        LEFT JOIN station_routes sr ON s.id = sr.station_id
        WHERE s.id = 1
        ORDER BY sr.line, sr.sub_line
    """)
    tokyo_routes = cursor.fetchall()
    for route in tokyo_routes:
        if route[3]:
            print(f"  {route[1]} ({route[2]}): {route[3]} {route[4]} - {route[5]}km")
        else:
            print(f"  {route[1]} ({route[2]}): ルート情報なし")

    print("\n運賃テーブル（サンプル）:")
    cursor.execute("SELECT min_distance_km, fare FROM fare_table ORDER BY min_distance_km LIMIT 10")
    fares = cursor.fetchall()
    for fare in fares:
        print(f"  {fare[0]}km以上: {fare[1]}円")

    conn.close()
    print("\n✓ 駅データの再構築が完了しました")
    print("\n注意: 既存のトリップデータと定期券データは削除されました")

if __name__ == "__main__":
    main()
