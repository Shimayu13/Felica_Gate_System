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

        # 既存データをクリア（強制再作成）
        print("🗑️  既存データをクリア中...")
        db.query(models.Gate).delete()
        db.query(models.Station).delete()
        db.query(models.Card).delete()
        db.query(models.User).delete()
        db.commit()

        # ユーザーの作成
        users = [
            models.User(id=1, name="田中太郎", email="tanaka@example.com", balance=Decimal("5000.00"), qr_token="QR_TANAKA_001", card_idm="0123456789ABCDEF"),
            models.User(id=2, name="佐藤花子", email="sato@example.com", balance=Decimal("3000.00"), qr_token="QR_SATO_001", card_idm="FEDCBA9876543210"),
            models.User(id=3, name="鈴木一郎", email="suzuki@example.com", balance=Decimal("10000.00"), qr_token="QR_SUZUKI_001"),
            models.User(id=4, name="高橋美咲", email="takahashi@example.com", balance=Decimal("2000.00"), qr_token="QR_TAKAHASHI_001"),
        ]
        db.add_all(users)
        db.commit()
        print(f"✓ {len(users)}人のユーザーを作成しました")

        # カードの作成
        cards = [
            models.Card(id=1, user_id=1, idm="0123456789ABCDEF", qr_token="QR_TANAKA_001", label="田中さんのFeliCa"),
            models.Card(id=2, user_id=2, idm="FEDCBA9876543210", qr_token="QR_SATO_001", label="佐藤さんのFeliCa"),
            models.Card(id=3, user_id=3, qr_token="QR_SUZUKI_001", label="鈴木さんのQRカード"),
            models.Card(id=4, user_id=4, qr_token="QR_TAKAHASHI_001", label="高橋さんのQRカード"),
        ]
        db.add_all(cards)
        db.commit()
        print(f"✓ {len(cards)}枚のカードを作成しました")

        # 駅の作成
        stations = [
            models.Station(id=1, code="STATION_1", name="新宿駅"),
            models.Station(id=2, code="STATION_2", name="渋谷駅"),
            models.Station(id=3, code="STATION_3", name="池袋駅"),
            models.Station(id=4, code="STATION_4", name="東京駅"),
        ]
        db.add_all(stations)
        db.commit()
        print(f"✓ {len(stations)}駅を作成しました")

        # ゲートの作成
        gates = [
            models.Gate(id=1, code="STATION_1_IN", station_id=1, name="新宿駅 入口1"),
            models.Gate(id=2, code="STATION_1_OUT", station_id=1, name="新宿駅 出口1"),
            models.Gate(id=3, code="STATION_2_IN", station_id=2, name="渋谷駅 入口1"),
            models.Gate(id=4, code="STATION_2_OUT", station_id=2, name="渋谷駅 出口1"),
            models.Gate(id=5, code="STATION_3_IN", station_id=3, name="池袋駅 入口1"),
            models.Gate(id=6, code="STATION_3_OUT", station_id=3, name="池袋駅 出口1"),
            models.Gate(id=7, code="STATION_4_IN", station_id=4, name="東京駅 入口1"),
            models.Gate(id=8, code="STATION_4_OUT", station_id=4, name="東京駅 出口1"),
        ]
        db.add_all(gates)
        db.commit()
        print(f"✓ {len(gates)}個のゲートを作成しました")

        print("\n✅ シードデータの投入が完了しました！")
        print("\n" + "=" * 60)
        print("📊 作成されたデータ:")
        print("=" * 60)
        print("\n👤 テストユーザー:")
        for user in users:
            print(f"   ID={user.id}, 名前={user.name}, 残高=¥{user.balance}, QRトークン={user.qr_token}")

        print("\n💳 カード:")
        for card in cards:
            print(f"   ID={card.id}, ユーザーID={card.user_id}, QRトークン={card.qr_token}")

        print("\n" + "=" * 60)
        print("🔔 次のステップ:")
        print("=" * 60)
        print("1. 顔認証を登録してください")
        print("   - ユーザーID 4 (高橋美咲) で顔認証を登録")
        print("   - ユーザーアプリの顔認証登録機能を使用")
        print("\n2. 改札アプリでテストしてください")
        print("   - QR→QR: QR_TAKAHASHI_001 で入場・退場")
        print("   - QR→顔: QR_TAKAHASHI_001 で入場、顔で退場")
        print("   - 顔→QR: 顔で入場、QR_TAKAHASHI_001 で退場")
        print("   - 顔→顔: 顔で入場・退場")
        print("=" * 60)

    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
