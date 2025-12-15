"""
多線区定期券の修正テスト
Tests for multi-line pass fixes:
1. Same-station entry/exit within pass area
2. Mid-section journeys within pass area (e.g., 横浜→新横浜)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_scan_request(qr_token, station_code, gate_code):
    """スキャンリクエストを作成"""
    return {
        "scan_source": "qr",
        "qr_token": qr_token,
        "station_code": station_code,
        "gate_code": gate_code,
        "timestamp": datetime.now().isoformat(),
        "device_id": "test_device"
    }

def test_same_station(qr_token):
    """Test 1: 同一駅での入出場（戸塚→戸塚）"""
    print("\n" + "="*80)
    print("Test 1: 同一駅での入出場（戸塚→戸塚）")
    print("="*80)

    # 戸塚で入場
    print("\n[入場] 戸塚 (STATION_18)")
    entry_req = create_scan_request(qr_token, "STATION_18", "STATION_18_IN")
    entry_resp = requests.post(f"{BASE_URL}/scan", json=entry_req)
    print(f"Status: {entry_resp.status_code}")
    print(f"Response: {json.dumps(entry_resp.json(), indent=2, ensure_ascii=False)}")

    # 戸塚で出場（同一駅）
    print("\n[出場] 戸塚 (STATION_18) - 同一駅")
    exit_req = create_scan_request(qr_token, "STATION_18", "STATION_18_OUT")
    exit_resp = requests.post(f"{BASE_URL}/scan", json=exit_req)
    print(f"Status: {exit_resp.status_code}")
    print(f"Response: {json.dumps(exit_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if exit_resp.status_code == 200:
        data = exit_resp.json()
        usage_amount = data.get("usage_amount", 0)
        if usage_amount == 0:
            print("\n✅ Test 1 PASSED: 同一駅での入出場は運賃0円")
        else:
            print(f"\n❌ Test 1 FAILED: 運賃が{usage_amount}円かかっています（期待値: 0円）")
    else:
        print(f"\n❌ Test 1 FAILED: Error {exit_resp.status_code}")

def test_mid_section_within_pass(qr_token):
    """Test 2: 定期券区間内の中間区間（横浜→新横浜）"""
    print("\n" + "="*80)
    print("Test 2: 定期券区間内の中間区間（横浜→新横浜）")
    print("="*80)
    print("定期券: 淵野辺(STATION_51)⇔戸塚(STATION_18)")
    print("区間2: 東神奈川→戸塚 (東海道線)")
    print("  ├─ 横浜 (STATION_15)")
    print("  └─ 新横浜 (STATION_42)")

    # 横浜で入場
    print("\n[入場] 横浜 (STATION_15)")
    entry_req = create_scan_request(qr_token, "STATION_15", "STATION_15_IN")
    entry_resp = requests.post(f"{BASE_URL}/scan", json=entry_req)
    print(f"Status: {entry_resp.status_code}")
    print(f"Response: {json.dumps(entry_resp.json(), indent=2, ensure_ascii=False)}")

    # 新横浜で出場
    print("\n[出場] 新横浜 (STATION_42)")
    exit_req = create_scan_request(qr_token, "STATION_42", "STATION_42_OUT")
    exit_resp = requests.post(f"{BASE_URL}/scan", json=exit_req)
    print(f"Status: {exit_resp.status_code}")
    print(f"Response: {json.dumps(exit_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if exit_resp.status_code == 200:
        data = exit_resp.json()
        usage_amount = data.get("usage_amount", 0)
        if usage_amount == 0:
            print("\n✅ Test 2 PASSED: 定期券区間内の中間区間は運賃0円")
        else:
            print(f"\n❌ Test 2 FAILED: 運賃が{usage_amount}円かかっています（期待値: 0円）")
    else:
        print(f"\n❌ Test 2 FAILED: Error {exit_resp.status_code}")

def test_another_mid_section(qr_token):
    """Test 3: 定期券区間内の別の中間区間（東神奈川→横浜）"""
    print("\n" + "="*80)
    print("Test 3: 定期券区間内の別の中間区間（東神奈川→横浜）")
    print("="*80)

    # 東神奈川で入場
    print("\n[入場] 東神奈川 (STATION_14)")
    entry_req = create_scan_request(qr_token, "STATION_14", "STATION_14_IN")
    entry_resp = requests.post(f"{BASE_URL}/scan", json=entry_req)
    print(f"Status: {entry_resp.status_code}")
    print(f"Response: {json.dumps(entry_resp.json(), indent=2, ensure_ascii=False)}")

    # 横浜で出場
    print("\n[出場] 横浜 (STATION_15)")
    exit_req = create_scan_request(qr_token, "STATION_15", "STATION_15_OUT")
    exit_resp = requests.post(f"{BASE_URL}/scan", json=exit_req)
    print(f"Status: {exit_resp.status_code}")
    print(f"Response: {json.dumps(exit_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if exit_resp.status_code == 200:
        data = exit_resp.json()
        usage_amount = data.get("usage_amount", 0)
        if usage_amount == 0:
            print("\n✅ Test 3 PASSED: 定期券区間内の中間区間は運賃0円")
        else:
            print(f"\n❌ Test 3 FAILED: 運賃が{usage_amount}円かかっています（期待値: 0円）")
    else:
        print(f"\n❌ Test 3 FAILED: Error {exit_resp.status_code}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("多線区定期券の修正テスト開始")
    print("="*80)
    print("ユーザー: user_id 4 (QR: QR_89239309D1916D5F)")
    print("定期券: 淵野辺(横浜線) ⇔ 戸塚(東海道線)")
    print("  区間1: 淵野辺→東神奈川 (横浜線)")
    print("  区間2: 東神奈川→戸塚 (東海道線)")

    # 正しいQRトークン
    qr_token = "QR_89239309D1916D5F"

    try:
        test_same_station(qr_token)
        test_mid_section_within_pass(qr_token)
        test_another_mid_section(qr_token)

        print("\n" + "="*80)
        print("全テスト完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
