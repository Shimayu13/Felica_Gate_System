#!/usr/bin/env python3
"""
営業距離ベースの運賃計算システムへの移行スクリプト

実行内容:
1. 古いテストデータ（ST01, ST02, ST03など）を削除
2. station_routesテーブルを作成
3. fare_tableテーブルを作成
4. CSVから営業距離データをインポート
5. CSVから運賃テーブルをインポート
"""

import sqlite3
import csv
import sys

DB_PATH = 'felica_gate.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== 営業距離ベースの運賃計算システムへの移行 ===\n")

    # ステップ1: 古いテストデータを削除
    print("[1/5] 古いテストデータを削除中...")
    cursor.execute("SELECT id, code, name FROM stations WHERE code LIKE 'ST%'")
    test_stations = cursor.fetchall()

    if test_stations:
        print(f"  削除対象の駅: {len(test_stations)}駅")
        for station in test_stations:
            print(f"    - ID {station[0]}: {station[2]} ({station[1]})")
            # 関連するゲートを削除
            cursor.execute("DELETE FROM gates WHERE station_id = ?", (station[0],))
            # 駅を削除
            cursor.execute("DELETE FROM stations WHERE id = ?", (station[0],))
        conn.commit()
        print(f"  ✓ {len(test_stations)}駅を削除しました")
    else:
        print("  削除対象のテストデータはありません")

    # ステップ2: station_routesテーブルを作成
    print("\n[2/5] station_routesテーブルを作成中...")
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
    conn.commit()
    print("  ✓ station_routesテーブルを作成しました")

    # ステップ3: fare_tableテーブルを作成
    print("\n[3/5] fare_tableテーブルを作成中...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fare_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            min_distance_km REAL NOT NULL UNIQUE,
            fare INTEGER NOT NULL
        )
    """)
    conn.commit()
    print("  ✓ fare_tableテーブルを作成しました")

    # ステップ4: 営業距離データをインポート
    print("\n[4/5] 営業距離データをインポート中...")
    try:
        with open('営業距離データ.csv', 'r', encoding='shift_jis') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ

            route_count = 0
            station_ids_in_csv = set()

            for row in reader:
                if not row[0]:
                    continue

                station_id = int(row[0])
                station_name = row[1]
                distance = float(row[2])
                line = row[3]
                sub_line = row[4]

                station_ids_in_csv.add(station_id)

                # station_routesにデータを追加（重複は無視）
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO station_routes
                        (station_id, line, sub_line, distance_from_origin)
                        VALUES (?, ?, ?, ?)
                    """, (station_id, line, sub_line, distance))
                    if cursor.rowcount > 0:
                        route_count += 1
                except Exception as e:
                    print(f"  警告: ID {station_id} ({station_name}) のルート追加に失敗: {e}")

            conn.commit()
            print(f"  ✓ {route_count}件のルート情報をインポートしました")
            print(f"  ✓ {len(station_ids_in_csv)}駅の営業距離データを処理しました")

    except FileNotFoundError:
        print("  エラー: 営業距離データ.csv が見つかりません")
        print("  server/営業距離データ.csv を配置してください")
        conn.close()
        sys.exit(1)
    except Exception as e:
        print(f"  エラー: {e}")
        conn.close()
        sys.exit(1)

    # ステップ5: 運賃テーブルをインポート
    print("\n[5/5] 運賃テーブルをインポート中...")
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
        print("  server/運賃体系.csv を配置してください")
        conn.close()
        sys.exit(1)
    except Exception as e:
        print(f"  エラー: {e}")
        conn.close()
        sys.exit(1)

    # 確認情報を表示
    print("\n=== 移行完了 ===")
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
    print("\n運賃テーブル（最初の10件）:")
    cursor.execute("SELECT min_distance_km, fare FROM fare_table ORDER BY min_distance_km LIMIT 10")
    fares = cursor.fetchall()
    for fare in fares:
        print(f"  {fare[0]}km以上: {fare[1]}円")

    print("\n駅ルート情報（サンプル: 東京駅）:")
    cursor.execute("""
        SELECT s.id, s.name, s.code, sr.line, sr.sub_line, sr.distance_from_origin
        FROM stations s
        LEFT JOIN station_routes sr ON s.id = sr.station_id
        WHERE s.name LIKE '%東京%'
        ORDER BY s.id, sr.line, sr.sub_line
    """)
    tokyo_routes = cursor.fetchall()
    for route in tokyo_routes:
        if route[3]:
            print(f"  {route[1]} ({route[2]}): {route[3]} {route[4]} - {route[5]}km")
        else:
            print(f"  {route[1]} ({route[2]}): ルート情報なし")

    conn.close()
    print("\n✓ 移行が正常に完了しました")

if __name__ == "__main__":
    main()
