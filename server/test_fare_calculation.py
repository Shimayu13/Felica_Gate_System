#!/usr/bin/env python3
"""
営業距離ベースの運賃計算のテストスクリプト
"""

import sqlite3
from decimal import Decimal

DB_PATH = 'felica_gate.db'

def get_fare_from_distance(distance_km: float) -> int:
    """
    営業キロから運賃を取得
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT fare FROM fare_table
        WHERE min_distance_km <= ?
        ORDER BY min_distance_km DESC
        LIMIT 1
        """,
        (distance_km,)
    )

    fare_entry = cursor.fetchone()
    conn.close()

    if fare_entry:
        return fare_entry[0]
    else:
        return 155  # デフォルト運賃


def calculate_station_distance(station_code_in: str, station_code_out: str):
    """
    2駅間の営業距離を計算
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 駅コードから駅IDを取得
    cursor.execute("SELECT id, name FROM stations WHERE code = ?", (station_code_in,))
    station_in = cursor.fetchone()

    cursor.execute("SELECT id, name FROM stations WHERE code = ?", (station_code_out,))
    station_out = cursor.fetchone()

    if not station_in or not station_out:
        conn.close()
        return None, None

    station_in_id, station_in_name = station_in
    station_out_id, station_out_name = station_out

    # 両駅のルート情報を取得
    cursor.execute(
        """
        SELECT line, sub_line, distance_from_origin
        FROM station_routes
        WHERE station_id = ?
        """,
        (station_in_id,)
    )
    routes_in = cursor.fetchall()

    cursor.execute(
        """
        SELECT line, sub_line, distance_from_origin
        FROM station_routes
        WHERE station_id = ?
        """,
        (station_out_id,)
    )
    routes_out = cursor.fetchall()

    conn.close()

    if not routes_in or not routes_out:
        return None, None

    # 最短距離を探す
    min_distance = None
    route_info = None

    # 同じ路線・同じ支線の組み合わせを優先
    for route_in in routes_in:
        line_in, sub_line_in, dist_in = route_in
        for route_out in routes_out:
            line_out, sub_line_out, dist_out = route_out

            # 同じ路線・同じ支線の場合
            if line_in == line_out and sub_line_in == sub_line_out:
                distance = abs(dist_out - dist_in)
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    route_info = f"{line_in} {sub_line_in}"

    # 同じ路線・同じ支線の組み合わせが見つからない場合
    if min_distance is None:
        min_dist_in = min(r[2] for r in routes_in)
        min_dist_out = min(r[2] for r in routes_out)
        min_distance = min_dist_in + min_dist_out
        route_info = "乗換"

    return min_distance, route_info


def test_fare_calculation():
    """
    運賃計算のテストケース
    """
    print("=== 営業距離ベース運賃計算テスト ===\n")

    # テストケース
    test_cases = [
        # (入場駅, 出場駅, 説明)
        ("STATION_1", "STATION_15", "東京 → 横浜"),
        ("STATION_1", "STATION_11", "東京 → 川崎"),
        ("STATION_1", "STATION_7", "東京 → 品川"),
        ("STATION_15", "STATION_19", "横浜 → 大船"),
        ("STATION_11", "STATION_15", "川崎 → 横浜"),
    ]

    print(f"{'経路':<30} {'営業キロ':<12} {'運賃':<10} {'使用路線'}")
    print("-" * 70)

    for station_in, station_out, description in test_cases:
        distance, route_info = calculate_station_distance(station_in, station_out)

        if distance is not None:
            fare = get_fare_from_distance(distance)
            print(f"{description:<30} {distance:>10.1f}km  ¥{fare:>7}  {route_info}")
        else:
            print(f"{description:<30} {'計算不可':<12} {'-':<10} {'-'}")

    # 運賃テーブルの確認
    print("\n\n=== 運賃テーブル ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT min_distance_km, fare FROM fare_table ORDER BY min_distance_km LIMIT 15")
    fares = cursor.fetchall()

    print(f"{'距離':<15} {'運賃'}")
    print("-" * 25)
    for i, (dist, fare) in enumerate(fares):
        next_dist = fares[i + 1][0] if i + 1 < len(fares) else "～"
        print(f"{dist}km ～ {next_dist}km {'未満' if isinstance(next_dist, float) else ''}".ljust(15) + f"¥{fare}")

    conn.close()


if __name__ == "__main__":
    test_fare_calculation()
