"""
シードデータを投入するスクリプト
テスト用のユーザー、カード、駅、ゲートを作成します
"""
from database import SessionLocal, engine, Base
import models
from decimal import Decimal

def seed_database():
    db = SessionLocal()

    try:
        # テーブルを作成
        Base.metadata.create_all(bind=engine)

        # 既存データの確認
        if db.query(models.User).count() > 0:
            print("データが既に存在します。スキップします。")
            return

        # ユーザーの作成
        users = [
            models.User(id=1, name="田中太郎", email="tanaka@example.com", balance=Decimal("5000.00"), qr_token="QR_TANAKA_001", card_idm="0123456789ABCDEF"),
            models.User(id=2, name="佐藤花子", email="sato@example.com", balance=Decimal("3000.00"), qr_token="QR_SATO_001", card_idm="FEDCBA9876543210"),
            models.User(id=3, name="鈴木一郎", email="suzuki@example.com", balance=Decimal("10000.00"), qr_token="QR_SUZUKI_001"),
        ]
        db.add_all(users)
        db.commit()
        print(f"✓ {len(users)}人のユーザーを作成しました")

        # カードの作成
        cards = [
            models.Card(id=1, user_id=1, idm="0123456789ABCDEF", qr_token="QR_TANAKA_001", label="田中さんのFeliCa"),
            models.Card(id=2, user_id=2, idm="FEDCBA9876543210", qr_token="QR_SATO_001", label="佐藤さんのFeliCa"),
            models.Card(id=3, user_id=3, qr_token="QR_SUZUKI_001", label="鈴木さんのQRカード"),
        ]
        db.add_all(cards)
        db.commit()
        print(f"✓ {len(cards)}枚のカードを作成しました")

        # 駅の作成
        stations = [
            models.Station(id=1, code="ST01", name="東京駅"),
            models.Station(id=2, code="ST02", name="新宿駅"),
            models.Station(id=3, code="ST03", name="渋谷駅"),
        ]
        db.add_all(stations)
        db.commit()
        print(f"✓ {len(stations)}駅を作成しました")

        # ゲートの作成
        gates = [
            models.Gate(id=1, code="A1", station_id=1, name="東京駅A1改札"),
            models.Gate(id=2, code="A2", station_id=1, name="東京駅A2改札"),
            models.Gate(id=3, code="B1", station_id=2, name="新宿駅B1改札"),
            models.Gate(id=4, code="B2", station_id=2, name="新宿駅B2改札"),
            models.Gate(id=5, code="C1", station_id=3, name="渋谷駅C1改札"),
        ]
        db.add_all(gates)
        db.commit()
        print(f"✓ {len(gates)}個のゲートを作成しました")

        print("\n✅ シードデータの投入が完了しました！")

    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
