"""
物販モードのテストスクリプト
Tests for retail purchase functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_retail_purchase_success():
    """Test 1: 正常な物販決済"""
    print("\n" + "="*80)
    print("Test 1: 正常な物販決済（¥500の購入）")
    print("="*80)

    qr_token = "QR_SUZUKI_001"  # 鈴木一郎
    amount = 500.0

    # ユーザーの残高を確認
    user_resp = requests.get(f"{BASE_URL}/users/3")
    user_data = user_resp.json()
    balance_before = user_data["balance"]
    print(f"\n購入前残高: ¥{balance_before}")

    # 物販決済リクエスト
    purchase_req = {
        "scan_source": "qr",
        "qr_token": qr_token,
        "amount": amount,
        "description": "テスト商品",
        "store_code": "STORE_1",
        "device_id": "test_device",
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n[決済リクエスト]")
    print(f"金額: ¥{amount}")
    print(f"商品: {purchase_req['description']}")

    purchase_resp = requests.post(f"{BASE_URL}/retail/purchase", json=purchase_req)
    print(f"\nStatus: {purchase_resp.status_code}")
    print(f"Response: {json.dumps(purchase_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if purchase_resp.status_code == 200:
        data = purchase_resp.json()
        if data.get("status") == "success":
            balance_after = data.get("balance_after", 0)
            print(f"\n✅ Test 1 PASSED: 決済成功")
            print(f"   購入前残高: ¥{balance_before}")
            print(f"   購入金額: ¥{amount}")
            print(f"   購入後残高: ¥{balance_after}")
            print(f"   差額: ¥{balance_before - balance_after}")
        else:
            print(f"\n❌ Test 1 FAILED: {data.get('message', 'Unknown error')}")
    else:
        print(f"\n❌ Test 1 FAILED: HTTP {purchase_resp.status_code}")

def test_retail_purchase_insufficient_balance():
    """Test 2: 残高不足の物販決済"""
    print("\n" + "="*80)
    print("Test 2: 残高不足の物販決済（¥100000の購入）")
    print("="*80)

    qr_token = "QR_SUZUKI_001"
    amount = 100000.0  # 残高を超える金額

    # ユーザーの残高を確認
    user_resp = requests.get(f"{BASE_URL}/users/3")
    user_data = user_resp.json()
    balance = user_data["balance"]
    print(f"\n現在残高: ¥{balance}")
    print(f"購入金額: ¥{amount}")

    # 物販決済リクエスト
    purchase_req = {
        "scan_source": "qr",
        "qr_token": qr_token,
        "amount": amount,
        "description": "高額商品",
        "store_code": "STORE_1",
        "device_id": "test_device",
        "timestamp": datetime.now().isoformat()
    }

    purchase_resp = requests.post(f"{BASE_URL}/retail/purchase", json=purchase_req)
    print(f"\nStatus: {purchase_resp.status_code}")
    print(f"Response: {json.dumps(purchase_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if purchase_resp.status_code == 200:
        data = purchase_resp.json()
        if data.get("status") == "error" and data.get("message") == "insufficient_balance":
            print(f"\n✅ Test 2 PASSED: 残高不足エラーが正しく返されました")
            print(f"   必要金額: ¥{data.get('required_amount', 0)}")
            print(f"   現在残高: ¥{data.get('current_balance', 0)}")
        else:
            print(f"\n❌ Test 2 FAILED: 予期しない応答")
    else:
        print(f"\n❌ Test 2 FAILED: HTTP {purchase_resp.status_code}")

def test_retail_purchase_invalid_card():
    """Test 3: 無効なQRトークンでの物販決済"""
    print("\n" + "="*80)
    print("Test 3: 無効なQRトークンでの物販決済")
    print("="*80)

    qr_token = "INVALID_QR_TOKEN"
    amount = 100.0

    # 物販決済リクエスト
    purchase_req = {
        "scan_source": "qr",
        "qr_token": qr_token,
        "amount": amount,
        "description": "テスト商品",
        "store_code": "STORE_1",
        "device_id": "test_device",
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n[決済リクエスト]")
    print(f"QRトークン: {qr_token}")
    print(f"金額: ¥{amount}")

    purchase_resp = requests.post(f"{BASE_URL}/retail/purchase", json=purchase_req)
    print(f"\nStatus: {purchase_resp.status_code}")
    print(f"Response: {json.dumps(purchase_resp.json(), indent=2, ensure_ascii=False)}")

    # 検証
    if purchase_resp.status_code == 200:
        data = purchase_resp.json()
        if data.get("status") == "error" and data.get("message") == "card_not_registered":
            print(f"\n✅ Test 3 PASSED: カード未登録エラーが正しく返されました")
        else:
            print(f"\n❌ Test 3 FAILED: 予期しない応答")
    else:
        print(f"\n❌ Test 3 FAILED: HTTP {purchase_resp.status_code}")

def test_get_purchases():
    """Test 4: 物販取引履歴の取得"""
    print("\n" + "="*80)
    print("Test 4: 物販取引履歴の取得")
    print("="*80)

    purchases_resp = requests.get(f"{BASE_URL}/purchases?limit=5")
    print(f"\nStatus: {purchases_resp.status_code}")

    if purchases_resp.status_code == 200:
        purchases = purchases_resp.json()
        print(f"\n取得件数: {len(purchases)}件")

        if len(purchases) > 0:
            print(f"\n最新の物販取引:")
            for i, purchase in enumerate(purchases[:3], 1):
                print(f"\n{i}. ID: {purchase['id']}")
                print(f"   ユーザーID: {purchase['user_id']}")
                print(f"   金額: ¥{purchase['amount']}")
                print(f"   商品: {purchase.get('description', 'N/A')}")
                print(f"   購入日時: {purchase['purchased_at']}")
            print(f"\n✅ Test 4 PASSED: 物販取引履歴を取得できました")
        else:
            print(f"\n⚠️  Test 4: 物販取引履歴がまだありません")
    else:
        print(f"\n❌ Test 4 FAILED: HTTP {purchases_resp.status_code}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("物販モードのテスト開始")
    print("="*80)

    try:
        test_retail_purchase_success()
        test_retail_purchase_insufficient_balance()
        test_retail_purchase_invalid_card()
        test_get_purchases()

        print("\n" + "="*80)
        print("全テスト完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
