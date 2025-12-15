#!/usr/bin/env python3
"""
エンドツーエンドテスト: ユーザー登録から改札通過まで
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'felica_gate.db'

def create_test_user():
    """
    テストユーザーとカードを作成
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テストユーザーを作成
    cursor.execute("""
        INSERT INTO users (name, email, balance, qr_token)
        VALUES (?, ?, ?, ?)
    """, ("テストユーザー", "test@example.com", 10000, "QR_TEST_001"))

    user_id = cursor.lastrowid

    # テストカードを作成
    cursor.execute("""
        INSERT INTO cards (user_id, qr_token, label)
        VALUES (?, ?, ?)
    """, (user_id, "QR_TEST_001", "テストユーザーのQRカード"))

    card_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(f"テストユーザーを作成しました: ID={user_id}, QR=QR_TEST_001")
    return user_id, card_id, "QR_TEST_001"


def simulate_gate_entry(qr_token, station_code):
    """
    改札入場をシミュレート
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # カードを取得
    cursor.execute("SELECT id, user_id FROM cards WHERE qr_token = ?", (qr_token,))
    card = cursor.fetchone()

    if not card:
        print(f"エラー: カードが見つかりません (QR={qr_token})")
        conn.close()
        return None

    card_id, user_id = card

    # 入場記録を作成
    cursor.execute("""
        INSERT INTO trips (user_id, card_id, station_in, gate_in, entered_at, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, card_id, station_code, f"{station_code}_IN", datetime.now(), "in_progress", datetime.now()))

    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 駅名を取得
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM stations WHERE code = ?", (station_code,))
    station = cursor.fetchone()
    station_name = station[0] if station else station_code
    conn.close()

    print(f"✓ 入場: {station_name} ({station_code})")
    return trip_id


def simulate_gate_exit(qr_token, station_code):
    """
    改札出場をシミュレート（運賃計算含む）
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # カードを取得
    cursor.execute("SELECT id, user_id FROM cards WHERE qr_token = ?", (qr_token,))
    card = cursor.fetchone()

    if not card:
        print(f"エラー: カードが見つかりません (QR={qr_token})")
        conn.close()
        return

    card_id, user_id = card

    # 進行中のトリップを取得
    cursor.execute("""
        SELECT id, station_in FROM trips
        WHERE card_id = ? AND status = 'in_progress'
        ORDER BY entered_at DESC
        LIMIT 1
    """, (card_id,))

    trip = cursor.fetchone()

    if not trip:
        print("エラー: 進行中のトリップが見つかりません")
        conn.close()
        return

    trip_id, station_in = trip

    # ユーザーの残高を取得
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    # 運賃計算（Pythonで直接計算）
    from test_fare_calculation import calculate_station_distance, get_fare_from_distance

    distance, route_info = calculate_station_distance(station_in, station_code)

    if distance is None:
        print("エラー: 運賃を計算できません")
        conn.close()
        return

    fare = get_fare_from_distance(distance)

    # 残高チェック
    if balance < fare:
        print(f"エラー: 残高不足 (必要: ¥{fare}, 残高: ¥{balance})")
        conn.close()
        return

    # 出場処理
    new_balance = balance - fare

    cursor.execute("""
        UPDATE trips
        SET station_out = ?,
            gate_out = ?,
            exited_at = ?,
            status = 'completed',
            fare_amount = ?,
            balance_before = ?,
            balance_after = ?
        WHERE id = ?
    """, (station_code, f"{station_code}_OUT", datetime.now(), fare, balance, new_balance, trip_id))

    cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))

    conn.commit()
    conn.close()

    # 駅名を取得
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM stations WHERE code = ?", (station_in,))
    station_in_info = cursor.fetchone()
    station_in_name = station_in_info[0] if station_in_info else station_in

    cursor.execute("SELECT name FROM stations WHERE code = ?", (station_code,))
    station_out_info = cursor.fetchone()
    station_out_name = station_out_info[0] if station_out_info else station_code
    conn.close()

    print(f"✓ 出場: {station_out_name} ({station_code})")
    print(f"  経路: {station_in_name} → {station_out_name}")
    print(f"  営業キロ: {distance:.1f}km ({route_info})")
    print(f"  運賃: ¥{fare}")
    print(f"  残高: ¥{balance} → ¥{new_balance}")


def main():
    print("=== エンドツーエンドテスト ===\n")

    # 既存のテストユーザーを削除
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE card_id IN (SELECT id FROM cards WHERE qr_token = 'QR_TEST_001')")
    cursor.execute("DELETE FROM cards WHERE qr_token = 'QR_TEST_001'")
    cursor.execute("DELETE FROM users WHERE qr_token = 'QR_TEST_001'")
    conn.commit()
    conn.close()

    # テストユーザーを作成
    user_id, card_id, qr_token = create_test_user()

    print("\n--- テストケース1: 東京 → 横浜 ---")
    simulate_gate_entry(qr_token, "STATION_1")  # 東京
    simulate_gate_exit(qr_token, "STATION_15")  # 横浜

    print("\n--- テストケース2: 横浜 → 川崎 ---")
    simulate_gate_entry(qr_token, "STATION_15")  # 横浜
    simulate_gate_exit(qr_token, "STATION_11")  # 川崎

    print("\n--- テストケース3: 川崎 → 品川 ---")
    simulate_gate_entry(qr_token, "STATION_11")  # 川崎
    simulate_gate_exit(qr_token, "STATION_7")  # 品川

    # 最終残高を確認
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    final_balance = cursor.fetchone()[0]
    conn.close()

    print(f"\n最終残高: ¥{final_balance}")
    print("\n✓ すべてのテストが完了しました")


if __name__ == "__main__":
    main()
