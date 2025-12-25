"""
シードデータを投入するスクリプト
テスト用のユーザー、カード、駅、ゲート、運賃表を作成します
"""
from database import SessionLocal, engine, Base
import models
from decimal import Decimal
import pandas as pd
from sqlalchemy import text

def seed_database():
    db = SessionLocal()

    try:
        # テーブルを作成
        Base.metadata.create_all(bind=engine)

        # 運賃表とルート情報のテーブルを作成
        print("🔧 運賃表・ルート情報テーブルを作成中...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS fare_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                min_distance_km INTEGER NOT NULL,
                fare INTEGER NOT NULL
            )
        """))

        db.execute(text("""
            CREATE TABLE IF NOT EXISTS station_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id INTEGER NOT NULL,
                line TEXT NOT NULL,
                sub_line TEXT,
                distance_from_origin REAL NOT NULL,
                FOREIGN KEY (station_id) REFERENCES stations(id)
            )
        """))
        db.commit()

        # 既存データをクリア（強制再作成）
        print("🗑️  既存データをクリア中...")
        db.execute(text("DELETE FROM fare_table"))
        db.execute(text("DELETE FROM station_routes"))
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

        # 運賃体系CSVからデータを読み込む
        print("📊 運賃体系データを読み込み中...")
        fare_df = pd.read_csv('運賃体系.csv', encoding='shift-jis')
        fare_count = 0
        for _, row in fare_df.iterrows():
            min_dist = row['最低距離']
            fare = row['運賃']
            if pd.notna(min_dist) and pd.notna(fare):
                db.execute(text("INSERT INTO fare_table (min_distance_km, fare) VALUES (:min_dist, :fare)"),
                          {"min_dist": int(min_dist), "fare": int(fare)})
                fare_count += 1
        db.commit()
        print(f"✓ {fare_count}件の運賃データを作成しました")

        # 営業距離データCSVから駅とルート情報を読み込む
        print("🚉 駅・ルートデータを読み込み中...")
        station_df = pd.read_csv('営業距離データ.csv', encoding='shift-jis')

        # 駅データを作成（重複を除く）
        unique_stations = station_df[['ID', '駅名']].drop_duplicates(subset=['ID'])
        stations = []
        for _, row in unique_stations.iterrows():
            station_id = int(row['ID'])
            station_name = row['駅名']
            station_code = f"STATION_{station_id}"
            stations.append(models.Station(id=station_id, code=station_code, name=station_name))

        db.add_all(stations)
        db.commit()
        print(f"✓ {len(stations)}駅を作成しました")

        # ルート情報を作成
        route_count = 0
        for _, row in station_df.iterrows():
            station_id = int(row['ID'])
            line = row['路線']
            sub_line = row['支線'] if pd.notna(row['支線']) else None
            distance_from_origin = float(row['起点駅からの営業キロ'])

            db.execute(text("""
                INSERT INTO station_routes (station_id, line, sub_line, distance_from_origin)
                VALUES (:station_id, :line, :sub_line, :distance_from_origin)
            """), {
                "station_id": station_id,
                "line": line,
                "sub_line": sub_line,
                "distance_from_origin": distance_from_origin
            })
            route_count += 1

        db.commit()
        print(f"✓ {route_count}件のルート情報を作成しました")

        # 全駅に改札を作成
        print("🚪 全駅に改札を作成中...")
        gates = []
        gate_id = 1
        for station in stations:
            # 各駅に1つの改札を設定
            gates.append(models.Gate(
                id=gate_id,
                code=f"GATE_{station.id}",
                station_id=station.id,
                name=f"{station.name} 改札"
            ))
            gate_id += 1

        db.add_all(gates)
        db.commit()
        print(f"✓ {len(gates)}個のゲートを作成しました（全{len(stations)}駅）")

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

        print(f"\n🚉 駅: {len(stations)}駅")
        print(f"🚪 改札: {len(gates)}個（全駅対応）")
        print(f"📊 運賃データ: {fare_count}件")
        print(f"🛤️  ルート情報: {route_count}件")

        # 主要駅を表示
        print("\n🚉 主要駅の例:")
        major_station_ids = [1, 7, 11, 15, 22]  # 東京、品川、川崎、横浜、武蔵小杉
        for station_id in major_station_ids:
            station = db.query(models.Station).filter(models.Station.id == station_id).first()
            if station:
                print(f"   {station.name} (GATE_{station.id})")

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
