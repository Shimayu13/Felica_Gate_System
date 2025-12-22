"""
顔認証APIのテストスクリプト

※注意: 実際の顔画像が必要です。
このスクリプトは顔画像ファイルをBase64エンコードしてAPIに送信します。
"""

import requests
import base64
import json
import os

BASE_URL = "http://localhost:8000"

def encode_image_to_base64(image_path):
    """画像ファイルをBase64エンコード"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def test_face_register(user_id, image_path):
    """顔登録テスト"""
    print("\n" + "="*80)
    print(f"顔登録テスト - ユーザーID: {user_id}")
    print("="*80)

    if not os.path.exists(image_path):
        print(f"❌ 画像ファイルが見つかりません: {image_path}")
        print("\n使い方:")
        print(f"  1. 顔写真（JPEG/PNG）を用意")
        print(f"  2. このスクリプトと同じディレクトリに配置")
        print(f"  3. ファイル名を指定して実行")
        return

    # 画像をBase64エンコード
    print(f"画像を読み込み中: {image_path}")
    base64_image = encode_image_to_base64(image_path)
    print(f"Base64エンコード完了: {len(base64_image)} 文字")

    # 顔登録リクエスト
    print(f"\n[POST] {BASE_URL}/face/register")
    response = requests.post(
        f"{BASE_URL}/face/register",
        json={
            "user_id": user_id,
            "face_image_base64": base64_image
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            print(f"\n✅ 顔登録成功!")
            print(f"   ユーザー: {data.get('user_name')}")
            print(f"   特徴量次元: {data.get('embedding_dim')}")
        else:
            print(f"\n❌ 顔登録失敗: {data.get('message')}")
    else:
        print(f"\n❌ エラー: HTTP {response.status_code}")

def test_face_verify(image_path):
    """顔認証テスト"""
    print("\n" + "="*80)
    print("顔認証テスト")
    print("="*80)

    if not os.path.exists(image_path):
        print(f"❌ 画像ファイルが見つかりません: {image_path}")
        return

    # 画像をBase64エンコード
    print(f"画像を読み込み中: {image_path}")
    base64_image = encode_image_to_base64(image_path)
    print(f"Base64エンコード完了: {len(base64_image)} 文字")

    # 顔認証リクエスト
    print(f"\n[POST] {BASE_URL}/face/verify")
    response = requests.post(
        f"{BASE_URL}/face/verify",
        json={
            "face_image_base64": base64_image
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        data = response.json()
        if data.get("verified"):
            print(f"\n✅ 顔認証成功!")
            print(f"   ユーザー: {data.get('user_name')} (ID: {data.get('user_id')})")
            print(f"   残高: ¥{data.get('balance')}")
            print(f"   距離: {data.get('distance'):.4f}")
            print(f"   類似度: {data.get('similarity'):.2f}%")
        else:
            print(f"\n❌ 顔認証失敗: {data.get('message')}")
    else:
        print(f"\n❌ エラー: HTTP {response.status_code}")

def test_with_sample_data():
    """サンプルデータでテスト（画像なし）"""
    print("\n" + "="*80)
    print("画像ファイルが必要です")
    print("="*80)
    print("\n顔認証APIを使用するには、実際の顔画像ファイルが必要です。")
    print("\n手順:")
    print("1. スマートフォンやカメラで自分の顔を撮影")
    print("2. 画像をこのディレクトリに保存（例: face.jpg）")
    print("3. 以下のコマンドを実行:")
    print("\n   # 顔を登録")
    print("   python test_face_recognition.py register 3 face.jpg")
    print("\n   # 顔認証")
    print("   python test_face_recognition.py verify face.jpg")
    print("\n注意:")
    print("- 正面を向いた明るい顔写真を使用してください")
    print("- 顔が画像の中央に大きく写るように調整してください")
    print("- JPEGまたはPNG形式が推奨されます")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # 引数なしの場合、使用方法を表示
        test_with_sample_data()
    elif sys.argv[1] == "register" and len(sys.argv) >= 4:
        # 顔登録: python test_face_recognition.py register <user_id> <image_path>
        user_id = int(sys.argv[2])
        image_path = sys.argv[3]
        test_face_register(user_id, image_path)
    elif sys.argv[1] == "verify" and len(sys.argv) >= 3:
        # 顔認証: python test_face_recognition.py verify <image_path>
        image_path = sys.argv[2]
        test_face_verify(image_path)
    else:
        print("使用方法:")
        print("  顔登録: python test_face_recognition.py register <user_id> <image_path>")
        print("  顔認証: python test_face_recognition.py verify <image_path>")
        print("\n例:")
        print("  python test_face_recognition.py register 3 face.jpg")
        print("  python test_face_recognition.py verify face.jpg")
