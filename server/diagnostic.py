"""
診断スクリプト - 顔認証と入退場記録の状態を確認
"""
from database import SessionLocal
import models
from sqlalchemy import text

def diagnose():
    db = SessionLocal()

    try:
        print("=" * 80)
        print("🔍 顔認証システム診断")
        print("=" * 80)

        # 1. 顔認証データの確認
        print("\n📸 登録済み顔認証データ:")
        print("-" * 80)
        face_data_list = db.query(models.FaceData).all()
        if face_data_list:
            for face_data in face_data_list:
                user = db.query(models.User).filter(models.User.id == face_data.user_id).first()
                print(f"  ユーザーID: {face_data.user_id}")
                print(f"  ユーザー名: {user.name if user else 'N/A'}")
                print(f"  登録日時: {face_data.registered_at}")
                print(f"  更新日時: {face_data.updated_at}")
                print(f"  有効状態: {'有効' if face_data.is_active == 1 else '無効'}")
                print(f"  顔データサイズ: {len(face_data.face_encoding)} bytes")
                print()
        else:
            print("  ⚠️  登録された顔認証データがありません")

        # 2. 進行中の入場記録（出場していないTrip）
        print("\n🚪 進行中の入場記録 (未出場):")
        print("-" * 80)
        in_progress_trips = db.query(models.Trip).filter(
            models.Trip.status == models.TripStatus.in_progress
        ).all()

        if in_progress_trips:
            for trip in in_progress_trips:
                user = db.query(models.User).filter(models.User.id == trip.user_id).first()
                card = db.query(models.Card).filter(models.Card.id == trip.card_id).first() if trip.card_id else None

                print(f"  Trip ID: {trip.id}")
                print(f"  ユーザーID: {trip.user_id} ({user.name if user else 'N/A'})")
                print(f"  カードID: {trip.card_id if trip.card_id else 'NULL (顔認証)'}")
                if card:
                    print(f"  カードQR: {card.qr_token}")
                print(f"  入場駅: {trip.station_in}")
                print(f"  入場ゲート: {trip.gate_in}")
                print(f"  入場日時: {trip.entered_at}")
                print(f"  状態: {trip.status}")
                print()
        else:
            print("  ✓ 進行中の入場記録はありません（全員出場済み）")

        # 3. 最近の完了した入退場記録
        print("\n📋 最近の完了した入退場記録（最新5件）:")
        print("-" * 80)
        completed_trips = db.query(models.Trip).filter(
            models.Trip.status == models.TripStatus.completed
        ).order_by(models.Trip.exited_at.desc()).limit(5).all()

        if completed_trips:
            for trip in completed_trips:
                user = db.query(models.User).filter(models.User.id == trip.user_id).first()
                print(f"  Trip ID: {trip.id}")
                print(f"  ユーザー: {user.name if user else 'N/A'} (ID: {trip.user_id})")
                print(f"  カードID: {trip.card_id if trip.card_id else 'NULL (顔認証)'}")
                print(f"  入場: {trip.station_in} ({trip.gate_in}) - {trip.entered_at}")
                print(f"  出場: {trip.station_out} ({trip.gate_out}) - {trip.exited_at}")
                print(f"  運賃: ¥{trip.fare_amount}")
                print(f"  残高: ¥{trip.balance_before} → ¥{trip.balance_after}")
                print()
        else:
            print("  完了した入退場記録がありません")

        # 4. ユーザー一覧と残高
        print("\n👤 ユーザー一覧:")
        print("-" * 80)
        users = db.query(models.User).all()
        for user in users:
            cards = db.query(models.Card).filter(models.Card.user_id == user.id).all()
            has_face_data = db.query(models.FaceData).filter(
                models.FaceData.user_id == user.id,
                models.FaceData.is_active == 1
            ).first() is not None

            print(f"  ID: {user.id} | 名前: {user.name} | 残高: ¥{user.balance}")
            print(f"    顔認証: {'✓ 登録済み' if has_face_data else '✗ 未登録'}")
            print(f"    カード数: {len(cards)}")
            for card in cards:
                print(f"      - QR: {card.qr_token}, IDm: {card.idm if card.idm else 'なし'}")
            print()

        # 5. ゲート情報サンプル
        print("\n🚪 ゲート情報（最初の10件）:")
        print("-" * 80)
        gates = db.query(models.Gate).limit(10).all()
        for gate in gates:
            station = db.query(models.Station).filter(models.Station.id == gate.station_id).first()
            print(f"  {gate.code} - {gate.name} (駅: {station.name if station else 'N/A'})")

        print("\n" + "=" * 80)
        print("✅ 診断完了")
        print("=" * 80)

        # 6. 推奨アクション
        print("\n💡 推奨アクション:")
        print("-" * 80)

        if not face_data_list:
            print("  ⚠️  顔認証データが登録されていません")
            print("     → ユーザーアプリで顔認証を登録してください")

        if in_progress_trips:
            print(f"  ⚠️  {len(in_progress_trips)}件の未出場記録があります")
            print("     → これらのユーザーは出場処理が可能です")
            for trip in in_progress_trips:
                user = db.query(models.User).filter(models.User.id == trip.user_id).first()
                print(f"       - {user.name if user else 'Unknown'} (ユーザーID: {trip.user_id})")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
