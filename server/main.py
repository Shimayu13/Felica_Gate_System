from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import os
import sqlite3
import base64

from database import engine, Base, get_db
import models
import schemas
import face_recognition as face_rec
import json

app = FastAPI(title="Felica Gate Server")

# CORS設定（管理画面からのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create tables if not exist (simple migration)
Base.metadata.create_all(bind=engine)


def get_fare_from_distance(distance_km: float, db: Session) -> Decimal:
    """
    営業キロから運賃を取得（fare_tableを使用）
    """
    print(f"\n💰 [運賃検索] 距離: {distance_km:.2f}km")

    # fare_tableから該当する運賃を検索
    # min_distance_km以上で最小のものを取得
    fare_entry = db.execute(
        text("""
        SELECT fare FROM fare_table
        WHERE min_distance_km <= :distance
        ORDER BY min_distance_km DESC
        LIMIT 1
        """),
        {"distance": distance_km}
    ).fetchone()

    if fare_entry:
        fare = Decimal(str(fare_entry[0]))
        print(f"💰 [運賃検索] 結果: ¥{fare}")
        return fare
    else:
        # デフォルト運賃（最低運賃）
        print(f"💰 [運賃検索] 結果: ¥155 (デフォルト運賃)")
        return Decimal("155")


def calculate_station_distance(station_code_in: str, station_code_out: str, db: Session) -> Optional[float]:
    """
    2駅間の営業距離を計算
    両駅の全ルートの組み合わせから最短距離を返す
    """
    print(f"\n📍 [距離計算] {station_code_in} → {station_code_out}")

    # 駅コードから駅IDを取得
    station_in = db.query(models.Station).filter(models.Station.code == station_code_in).first()
    station_out = db.query(models.Station).filter(models.Station.code == station_code_out).first()

    if not station_in or not station_out:
        print(f"❌ [距離計算] エラー: 駅が見つかりません")
        return None

    print(f"📍 [距離計算] 入場駅: {station_in.name} ({station_in.code})")
    print(f"📍 [距離計算] 出場駅: {station_out.name} ({station_out.code})")

    # 両駅のルート情報を取得
    routes_in = db.execute(
        text("""
        SELECT line, sub_line, distance_from_origin
        FROM station_routes
        WHERE station_id = :station_id
        """),
        {"station_id": station_in.id}
    ).fetchall()

    routes_out = db.execute(
        text("""
        SELECT line, sub_line, distance_from_origin
        FROM station_routes
        WHERE station_id = :station_id
        """),
        {"station_id": station_out.id}
    ).fetchall()

    if not routes_in or not routes_out:
        print(f"❌ [距離計算] エラー: ルート情報が見つかりません")
        return None

    print(f"\n🛤️  [入場駅ルート] {len(routes_in)}件:")
    for route in routes_in:
        line, sub_line, dist = route
        print(f"   - {line} {sub_line or ''}: {dist:.2f}km")

    print(f"\n🛤️  [出場駅ルート] {len(routes_out)}件:")
    for route in routes_out:
        line, sub_line, dist = route
        print(f"   - {line} {sub_line or ''}: {dist:.2f}km")

    # 最短距離を探す
    min_distance = None
    selected_route = None

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
                    selected_route = {
                        "line": line_in,
                        "sub_line": sub_line_in,
                        "dist_in": dist_in,
                        "dist_out": dist_out,
                        "type": "same_line"
                    }

    # 同じ路線・同じ支線の組み合わせが見つからない場合
    # 接続駅を経由した経路を探す
    if min_distance is None:
        print(f"\n🔍 [接続駅検索] 同一路線が見つからないため、接続駅を探します")

        # 入場駅と出場駅の両方に存在する路線を探す
        # (line, sub_line)のセットを作成
        lines_in = {(r[0], r[1]) for r in routes_in}
        lines_out = {(r[0], r[1]) for r in routes_out}

        # 接続駅経由の最短経路を探す
        # すべての駅を取得して、接続駅候補を探す
        all_stations = db.query(models.Station).all()

        best_route = None

        for junction_station in all_stations:
            # 接続駅が入場駅や出場駅と同じ場合はスキップ
            if junction_station.id == station_in.id or junction_station.id == station_out.id:
                continue

            # 接続駅のルート情報を取得
            routes_junction = db.execute(
                text("""
                SELECT line, sub_line, distance_from_origin
                FROM station_routes
                WHERE station_id = :station_id
                """),
                {"station_id": junction_station.id}
            ).fetchall()

            if not routes_junction:
                continue

            # 入場駅→接続駅の経路を探す
            for route_in in routes_in:
                line_in, sub_line_in, dist_in = route_in
                for route_junction_1 in routes_junction:
                    line_j1, sub_line_j1, dist_j1 = route_junction_1

                    # 同じ路線・同じ支線の場合
                    if line_in == line_j1 and sub_line_in == sub_line_j1:
                        dist_to_junction = abs(dist_j1 - dist_in)

                        # 接続駅→出場駅の経路を探す
                        for route_junction_2 in routes_junction:
                            line_j2, sub_line_j2, dist_j2 = route_junction_2
                            for route_out in routes_out:
                                line_out, sub_line_out, dist_out = route_out

                                # 同じ路線・同じ支線の場合
                                if line_j2 == line_out and sub_line_j2 == sub_line_out:
                                    dist_from_junction = abs(dist_out - dist_j2)
                                    total_distance = dist_to_junction + dist_from_junction

                                    if min_distance is None or total_distance < min_distance:
                                        min_distance = total_distance
                                        best_route = {
                                            "junction_station": junction_station.name,
                                            "junction_code": junction_station.code,
                                            "line_to_junction": line_in,
                                            "sub_line_to_junction": sub_line_in,
                                            "dist_to_junction": dist_to_junction,
                                            "line_from_junction": line_out,
                                            "sub_line_from_junction": sub_line_out,
                                            "dist_from_junction": dist_from_junction,
                                            "total_distance": total_distance,
                                            "type": "via_junction"
                                        }

        if best_route:
            selected_route = best_route
            print(f"\n✅ [接続駅経由] {best_route['junction_station']}駅を経由")
        else:
            # 接続駅が見つからない場合は、単純に距離を加算（フォールバック）
            print(f"\n⚠️  [経路選択] 接続駅が見つからないため、単純加算で計算")
            min_dist_in = min(r[2] for r in routes_in)
            min_dist_out = min(r[2] for r in routes_out)
            min_distance = min_dist_in + min_dist_out

            route_in_selected = [r for r in routes_in if r[2] == min_dist_in][0]
            route_out_selected = [r for r in routes_out if r[2] == min_dist_out][0]

            selected_route = {
                "line_in": route_in_selected[0],
                "sub_line_in": route_in_selected[1],
                "dist_in": min_dist_in,
                "line_out": route_out_selected[0],
                "sub_line_out": route_out_selected[1],
                "dist_out": min_dist_out,
                "type": "simple_sum"
            }

    if selected_route:
        if selected_route["type"] == "same_line":
            print(f"\n✅ [経路選択] {selected_route['line']} {selected_route['sub_line'] or ''}")
            print(f"   入場駅位置: {selected_route['dist_in']:.2f}km")
            print(f"   出場駅位置: {selected_route['dist_out']:.2f}km")
            print(f"   駅間距離: {min_distance:.2f}km")
        elif selected_route["type"] == "via_junction":
            print(f"   {station_in.name} → {selected_route['junction_station']} → {station_out.name}")
            print(f"   第1区間: {selected_route['line_to_junction']} {selected_route['sub_line_to_junction'] or ''} ({selected_route['dist_to_junction']:.2f}km)")
            print(f"   第2区間: {selected_route['line_from_junction']} {selected_route['sub_line_from_junction'] or ''} ({selected_route['dist_from_junction']:.2f}km)")
            print(f"   合計距離: {min_distance:.2f}km")
        else:
            print(f"\n✅ [経路選択] 異なる路線での計算")
            print(f"   入場: {selected_route['line_in']} {selected_route['sub_line_in'] or ''} ({selected_route['dist_in']:.2f}km)")
            print(f"   出場: {selected_route['line_out']} {selected_route['sub_line_out'] or ''} ({selected_route['dist_out']:.2f}km)")
            print(f"   合計距離: {min_distance:.2f}km")

    return min_distance


def calculate_fare(station_in: Optional[str], station_out: Optional[str], db: Session = None) -> Decimal:
    """
    営業距離ベースの運賃計算
    station_in: 入場駅コード
    station_out: 出場駅コード
    db: データベースセッション（必須）
    """
    print(f"\n{'='*60}")
    print(f"🎫 [運賃計算開始] {station_in} → {station_out}")
    print(f"{'='*60}")

    if not station_in or not station_out or not db:
        # デフォルト運賃
        print(f"⚠️  [運賃計算] パラメータ不足 → デフォルト運賃 ¥155")
        print(f"{'='*60}\n")
        return Decimal("155")

    # 同じ駅の場合は最低運賃
    if station_in == station_out:
        print(f"ℹ️  [運賃計算] 同一駅 → 最低運賃 ¥155")
        print(f"{'='*60}\n")
        return Decimal("155")

    # 駅間距離を計算
    distance = calculate_station_distance(station_in, station_out, db)

    if distance is None:
        # 距離が計算できない場合はデフォルト運賃
        print(f"❌ [運賃計算] 距離計算失敗 → デフォルト運賃 ¥155")
        print(f"{'='*60}\n")
        return Decimal("155")

    # 距離から運賃を取得
    fare = get_fare_from_distance(distance, db)

    print(f"\n🎫 [運賃計算完了] {station_in} → {station_out}")
    print(f"   距離: {distance:.2f}km")
    print(f"   運賃: ¥{fare}")
    print(f"{'='*60}\n")

    return fare


def get_station_position_on_route(station_code: str, line: str, sub_line: str, db: Session) -> Optional[float]:
    """
    指定された路線上での駅の位置（起点からの距離）を取得
    """
    station = db.query(models.Station).filter(models.Station.code == station_code).first()
    if not station:
        return None

    route = db.execute(
        text("""
        SELECT distance_from_origin
        FROM station_routes
        WHERE station_id = :station_id AND line = :line AND sub_line = :sub_line
        """),
        {"station_id": station.id, "line": line, "sub_line": sub_line}
    ).fetchone()

    return route[0] if route else None


def calculate_fare_with_pass(user_id: int, station_in: str, station_out: str, db: Session) -> dict:
    """
    定期券を考慮した運賃計算
    定期券区間内の部分は運賃0円、区間外のみ運賃計算

    Returns:
        {
            "fare": Decimal,
            "used_pass": bool,
            "pass_id": int or None,
            "pass_type": str or None,
            "covered_section": str or None,  # 定期券でカバーされた区間
            "charged_section": str or None    # 運賃が発生した区間
        }
    """
    now = datetime.utcnow()

    print(f"\n🎫 [定期券チェック] {station_in} → {station_out}")

    # ユーザーのアクティブな定期券を取得
    passes = db.query(models.Pass).filter(
        models.Pass.user_id == user_id,
        models.Pass.is_active == 1,
        models.Pass.valid_from <= now,
        models.Pass.valid_until >= now
    ).all()

    if not passes:
        print(f"   定期券なし → 通常運賃計算")
        fare = calculate_fare(station_in, station_out, db)
        return {
            "fare": fare,
            "used_pass": False,
            "pass_id": None,
            "pass_type": None,
            "covered_section": None,
            "charged_section": f"{station_in}→{station_out}"
        }

    best_result = None
    min_fare = None

    for pass_obj in passes:
        print(f"\n   定期券チェック: {pass_obj.station_from} ⇔ {pass_obj.station_to} ({pass_obj.pass_type})")

        # 定期券の駅情報を取得
        pass_from = db.query(models.Station).filter(models.Station.code == pass_obj.station_from).first()
        pass_to = db.query(models.Station).filter(models.Station.code == pass_obj.station_to).first()
        journey_in = db.query(models.Station).filter(models.Station.code == station_in).first()
        journey_out = db.query(models.Station).filter(models.Station.code == station_out).first()

        if not all([pass_from, pass_to, journey_in, journey_out]):
            continue

        # 定期券区間のルート情報を取得
        pass_from_routes = db.execute(
            text("""
            SELECT line, sub_line, distance_from_origin
            FROM station_routes
            WHERE station_id = :station_id
            """),
            {"station_id": pass_from.id}
        ).fetchall()

        pass_to_routes = db.execute(
            text("""
            SELECT line, sub_line, distance_from_origin
            FROM station_routes
            WHERE station_id = :station_id
            """),
            {"station_id": pass_to.id}
        ).fetchall()

        # まず、定期券の両駅が共通して持つ路線を探す（直通の場合）
        found_direct_route = False

        for route_from in pass_from_routes:
            line_from, sub_line_from, dist_from = route_from
            for route_to in pass_to_routes:
                line_to, sub_line_to, dist_to = route_to

                if line_from == line_to and sub_line_from == sub_line_to:
                    found_direct_route = True
                    # この路線上で定期券が有効
                    pass_line = line_from
                    pass_sub_line = sub_line_from
                    pass_start_km = min(dist_from, dist_to)
                    pass_end_km = max(dist_from, dist_to)

                    print(f"      路線: {pass_line} {pass_sub_line or ''}")
                    print(f"      定期区間: {pass_start_km:.2f}km～{pass_end_km:.2f}km")

                    # 乗車駅と降車駅のこの路線上での位置を取得
                    journey_in_pos = get_station_position_on_route(station_in, pass_line, pass_sub_line, db)
                    journey_out_pos = get_station_position_on_route(station_out, pass_line, pass_sub_line, db)

                    if journey_in_pos is None or journey_out_pos is None:
                        print(f"      ✗ 乗車区間がこの路線上にありません")
                        continue

                    journey_start_km = min(journey_in_pos, journey_out_pos)
                    journey_end_km = max(journey_in_pos, journey_out_pos)

                    print(f"      乗車区間: {journey_start_km:.2f}km～{journey_end_km:.2f}km")

                    # 重複区間を計算
                    overlap_start = max(pass_start_km, journey_start_km)
                    overlap_end = min(pass_end_km, journey_end_km)

                    if overlap_start < overlap_end:
                        # 重複あり
                        overlap_distance = overlap_end - overlap_start
                        print(f"      ✓ 定期適用区間: {overlap_start:.2f}km～{overlap_end:.2f}km ({overlap_distance:.2f}km)")

                        # 定期券でカバーされない区間の距離を計算
                        uncovered_distance = 0.0
                        charged_sections = []

                        # 乗車駅側のはみ出し
                        if journey_start_km < overlap_start:
                            section_dist = overlap_start - journey_start_km
                            uncovered_distance += section_dist
                            charged_sections.append(f"前方{section_dist:.2f}km")
                            print(f"      運賃計算区間（前方）: {section_dist:.2f}km")

                        # 降車駅側のはみ出し
                        if journey_end_km > overlap_end:
                            section_dist = journey_end_km - overlap_end
                            uncovered_distance += section_dist
                            charged_sections.append(f"後方{section_dist:.2f}km")
                            print(f"      運賃計算区間（後方）: {section_dist:.2f}km")

                        if uncovered_distance == 0:
                            # 完全に定期券内
                            print(f"      ✓ 完全に定期券区間内 → 運賃0円")
                            return {
                                "fare": Decimal(0),
                                "used_pass": True,
                                "pass_id": pass_obj.id,
                                "pass_type": pass_obj.pass_type,
                                "covered_section": f"{station_in}→{station_out}",
                                "charged_section": None
                            }
                        else:
                            # 部分的にカバー
                            fare = get_fare_from_distance(uncovered_distance, db)
                            print(f"      運賃計算距離: {uncovered_distance:.2f}km → ¥{fare}")

                            if min_fare is None or fare < min_fare:
                                min_fare = fare
                                best_result = {
                                    "fare": fare,
                                    "used_pass": True,
                                    "pass_id": pass_obj.id,
                                    "pass_type": pass_obj.pass_type,
                                    "covered_section": f"{overlap_distance:.2f}km",
                                    "charged_section": "+".join(charged_sections)
                                }
                    else:
                        print(f"      ✗ 定期券区間と重複なし")

        # 直通路線が見つからなかった場合、接続駅経由の定期券として処理
        if not found_direct_route:
            print(f"      定期券の両端が異なる路線にあります。接続駅経由で計算します。")

            # 同一駅チェック
            if station_in == station_out:
                print(f"      ✓ 同一駅での入出場 → 運賃0円")
                return {
                    "fare": Decimal(0),
                    "used_pass": True,
                    "pass_id": pass_obj.id,
                    "pass_type": pass_obj.pass_type,
                    "covered_section": f"{station_in}",
                    "charged_section": None
                }

            # 完全一致チェック
            if ((journey_in.id == pass_from.id and journey_out.id == pass_to.id) or
                (journey_in.id == pass_to.id and journey_out.id == pass_from.id)):
                print(f"      ✓ 定期券区間と完全一致 → 運賃0円")
                return {
                    "fare": Decimal(0),
                    "used_pass": True,
                    "pass_id": pass_obj.id,
                    "pass_type": pass_obj.pass_type,
                    "covered_section": f"{station_in}→{station_out}",
                    "charged_section": None
                }

            # 接続駅を見つけて、両駅が定期券区間内にあるかチェック
            # 接続駅経由の部分適用を計算
            # 接続駅を見つける（定期券の両端の路線を持つ駅）
            all_stations = db.query(models.Station).all()

            for junction_station in all_stations:
                # 接続駅のルート情報を取得
                routes_junction = db.execute(
                    text("""
                    SELECT line, sub_line, distance_from_origin
                    FROM station_routes
                    WHERE station_id = :station_id
                    """),
                    {"station_id": junction_station.id}
                ).fetchall()

                if not routes_junction:
                    continue

                # 接続駅が定期券の両端の路線を持つかチェック
                junction_lines = {(r[0], r[1]) for r in routes_junction}
                pass_from_lines = {(r[0], r[1]) for r in pass_from_routes}
                pass_to_lines = {(r[0], r[1]) for r in pass_to_routes}

                # 接続駅が pass_from の路線と pass_to の路線の両方を持つ必要がある
                has_from_line = bool(junction_lines & pass_from_lines)
                has_to_line = bool(junction_lines & pass_to_lines)

                if not (has_from_line and has_to_line):
                    continue

                # この接続駅を使って定期券を2つの区間に分割
                # 区間1: pass_from → junction (on line1)
                # 区間2: junction → pass_to (on line2)

                for route_from in pass_from_routes:
                    line_from, sub_line_from, dist_from = route_from
                    for route_j1 in routes_junction:
                        line_j1, sub_line_j1, dist_j1 = route_j1

                        if line_from != line_j1 or sub_line_from != sub_line_j1:
                            continue

                        # 区間1の範囲
                        pass_seg1_start = min(dist_from, dist_j1)
                        pass_seg1_end = max(dist_from, dist_j1)

                        # 乗車経路がこの区間1上にあるかチェック
                        journey_in_pos_seg1 = get_station_position_on_route(station_in, line_from, sub_line_from, db)
                        journey_out_pos_seg1 = get_station_position_on_route(station_out, line_from, sub_line_from, db)

                        if journey_in_pos_seg1 is not None and journey_out_pos_seg1 is not None:
                            # 両方の駅がこの路線上にある
                            journey_start = min(journey_in_pos_seg1, journey_out_pos_seg1)
                            journey_end = max(journey_in_pos_seg1, journey_out_pos_seg1)

                            # 重複区間を計算
                            overlap_start = max(pass_seg1_start, journey_start)
                            overlap_end = min(pass_seg1_end, journey_end)

                            if overlap_start < overlap_end:
                                # 区間1で重複あり
                                covered_dist = overlap_end - overlap_start
                                total_journey_dist = journey_end - journey_start
                                uncovered_dist = total_journey_dist - covered_dist

                                print(f"      ✓ 接続駅: {junction_station.name}")
                                print(f"      定期区間1: {line_from} {sub_line_from or ''} ({pass_seg1_start:.2f}～{pass_seg1_end:.2f}km)")
                                print(f"      乗車区間: {journey_start:.2f}～{journey_end:.2f}km")
                                print(f"      定期適用: {covered_dist:.2f}km / 運賃計算: {uncovered_dist:.2f}km")

                                if uncovered_dist == 0:
                                    return {
                                        "fare": Decimal(0),
                                        "used_pass": True,
                                        "pass_id": pass_obj.id,
                                        "pass_type": pass_obj.pass_type,
                                        "covered_section": f"{station_in}→{station_out}",
                                        "charged_section": None
                                    }
                                else:
                                    fare = get_fare_from_distance(uncovered_dist, db)
                                    if min_fare is None or fare < min_fare:
                                        min_fare = fare
                                        best_result = {
                                            "fare": fare,
                                            "used_pass": True,
                                            "pass_id": pass_obj.id,
                                            "pass_type": pass_obj.pass_type,
                                            "covered_section": f"{covered_dist:.2f}km",
                                            "charged_section": f"{uncovered_dist:.2f}km"
                                        }

                        # 区間2をチェック
                        for route_to in pass_to_routes:
                            line_to, sub_line_to, dist_to = route_to
                            for route_j2 in routes_junction:
                                line_j2, sub_line_j2, dist_j2 = route_j2

                                if line_to != line_j2 or sub_line_to != sub_line_j2:
                                    continue

                                # 区間2の範囲
                                pass_seg2_start = min(dist_to, dist_j2)
                                pass_seg2_end = max(dist_to, dist_j2)

                                # 乗車経路がこの区間2上にあるかチェック
                                journey_in_pos_seg2 = get_station_position_on_route(station_in, line_to, sub_line_to, db)
                                journey_out_pos_seg2 = get_station_position_on_route(station_out, line_to, sub_line_to, db)

                                if journey_in_pos_seg2 is not None and journey_out_pos_seg2 is not None:
                                    # 両方の駅がこの路線上にある
                                    journey_start = min(journey_in_pos_seg2, journey_out_pos_seg2)
                                    journey_end = max(journey_in_pos_seg2, journey_out_pos_seg2)

                                    # 重複区間を計算
                                    overlap_start = max(pass_seg2_start, journey_start)
                                    overlap_end = min(pass_seg2_end, journey_end)

                                    if overlap_start < overlap_end:
                                        # 区間2で重複あり
                                        covered_dist = overlap_end - overlap_start
                                        total_journey_dist = journey_end - journey_start
                                        uncovered_dist = total_journey_dist - covered_dist

                                        print(f"      ✓ 接続駅: {junction_station.name}")
                                        print(f"      定期区間2: {line_to} {sub_line_to or ''} ({pass_seg2_start:.2f}～{pass_seg2_end:.2f}km)")
                                        print(f"      乗車区間: {journey_start:.2f}～{journey_end:.2f}km")
                                        print(f"      定期適用: {covered_dist:.2f}km / 運賃計算: {uncovered_dist:.2f}km")

                                        if uncovered_dist == 0:
                                            return {
                                                "fare": Decimal(0),
                                                "used_pass": True,
                                                "pass_id": pass_obj.id,
                                                "pass_type": pass_obj.pass_type,
                                                "covered_section": f"{station_in}→{station_out}",
                                                "charged_section": None
                                            }
                                        else:
                                            fare = get_fare_from_distance(uncovered_dist, db)
                                            if min_fare is None or fare < min_fare:
                                                min_fare = fare
                                                best_result = {
                                                    "fare": fare,
                                                    "used_pass": True,
                                                    "pass_id": pass_obj.id,
                                                    "pass_type": pass_obj.pass_type,
                                                    "covered_section": f"{covered_dist:.2f}km",
                                                    "charged_section": f"{uncovered_dist:.2f}km"
                                                }

            # 接続駅経由の計算で結果が得られなかった場合、
            # 両駅が定期券区間内に完全に含まれるかチェック
            if not best_result and not min_fare:
                print(f"      両駅が定期券区間内に含まれるかチェックします")

                # 接続駅を探す
                for junction_station in all_stations:
                    routes_junction = db.execute(
                        text("""
                        SELECT line, sub_line, distance_from_origin
                        FROM station_routes
                        WHERE station_id = :station_id
                        """),
                        {"station_id": junction_station.id}
                    ).fetchall()

                    if not routes_junction:
                        continue

                    junction_lines = {(r[0], r[1]) for r in routes_junction}
                    pass_from_lines = {(r[0], r[1]) for r in pass_from_routes}
                    pass_to_lines = {(r[0], r[1]) for r in pass_to_routes}

                    has_from_line = bool(junction_lines & pass_from_lines)
                    has_to_line = bool(junction_lines & pass_to_lines)

                    if not (has_from_line and has_to_line):
                        continue

                    # 接続駅が見つかった
                    # 定期券を2つの区間に分割
                    for route_from in pass_from_routes:
                        line_from, sub_line_from, dist_from = route_from
                        for route_j1 in routes_junction:
                            line_j1, sub_line_j1, dist_j1 = route_j1

                            if line_from != line_j1 or sub_line_from != sub_line_j1:
                                continue

                            # 区間1: pass_from → junction
                            pass_seg1_start = min(dist_from, dist_j1)
                            pass_seg1_end = max(dist_from, dist_j1)

                            for route_to in pass_to_routes:
                                line_to, sub_line_to, dist_to = route_to
                                for route_j2 in routes_junction:
                                    line_j2, sub_line_j2, dist_j2 = route_j2

                                    if line_to != line_j2 or sub_line_to != sub_line_j2:
                                        continue

                                    # 区間2: junction → pass_to
                                    pass_seg2_start = min(dist_to, dist_j2)
                                    pass_seg2_end = max(dist_to, dist_j2)

                                    # 乗車駅が区間1または区間2に含まれるかチェック
                                    journey_in_pos_seg1 = get_station_position_on_route(station_in, line_from, sub_line_from, db)
                                    journey_in_pos_seg2 = get_station_position_on_route(station_in, line_to, sub_line_to, db)

                                    # 降車駅が区間1または区間2に含まれるかチェック
                                    journey_out_pos_seg1 = get_station_position_on_route(station_out, line_from, sub_line_from, db)
                                    journey_out_pos_seg2 = get_station_position_on_route(station_out, line_to, sub_line_to, db)

                                    # 乗車駅がいずれかの区間に含まれるか
                                    in_in_seg1 = journey_in_pos_seg1 is not None and pass_seg1_start <= journey_in_pos_seg1 <= pass_seg1_end
                                    in_in_seg2 = journey_in_pos_seg2 is not None and pass_seg2_start <= journey_in_pos_seg2 <= pass_seg2_end

                                    # 降車駅がいずれかの区間に含まれるか
                                    out_in_seg1 = journey_out_pos_seg1 is not None and pass_seg1_start <= journey_out_pos_seg1 <= pass_seg1_end
                                    out_in_seg2 = journey_out_pos_seg2 is not None and pass_seg2_start <= journey_out_pos_seg2 <= pass_seg2_end

                                    # 両方の駅が定期券区間内（どちらかの区間）に含まれる場合
                                    if (in_in_seg1 or in_in_seg2) and (out_in_seg1 or out_in_seg2):
                                        print(f"      ✓ 接続駅: {junction_station.name}")
                                        print(f"      ✓ 両駅が定期券区間内 → 運賃0円")
                                        print(f"      入場駅: {'区間1' if in_in_seg1 else '区間2'} ({station_in})")
                                        print(f"      出場駅: {'区間1' if out_in_seg1 else '区間2'} ({station_out})")
                                        return {
                                            "fare": Decimal(0),
                                            "used_pass": True,
                                            "pass_id": pass_obj.id,
                                            "pass_type": pass_obj.pass_type,
                                            "covered_section": f"{station_in}→{station_out}",
                                            "charged_section": None
                                        }

    if best_result:
        print(f"\n   ✓ 最適な定期券適用: ¥{best_result['fare']}")
        return best_result

    # どの定期券も適用できない場合は通常運賃
    print(f"\n   定期券適用不可 → 通常運賃計算")
    fare = calculate_fare(station_in, station_out, db)
    return {
        "fare": fare,
        "used_pass": False,
        "pass_id": None,
        "pass_type": None,
        "covered_section": None,
        "charged_section": f"{station_in}→{station_out}"
    }


@app.post("/scan")
def scan(req: schemas.ScanRequest, db: Session = Depends(get_db)):
    # find card by idm or qr
    card = None
    if req.scan_source == "felica" and req.card_idm:
        card = db.query(models.Card).filter(models.Card.idm == req.card_idm).first()
    elif req.scan_source == "qr" and req.qr_token:
        card = db.query(models.Card).filter(models.Card.qr_token == req.qr_token).first()
    else:
        raise HTTPException(status_code=400, detail="Missing card identifier for given scan_source")

    if not card:
        return {"status": "error", "message": "card_not_registered"}

    if not card.user:
        return {"status": "error", "message": "user_not_found_for_card"}

    # check in-progress trip
    in_trip = db.query(models.Trip).filter(models.Trip.card_id == card.id, models.Trip.status == models.TripStatus.in_progress).order_by(models.Trip.entered_at.desc()).first()

    if in_trip:
        # complete trip
        # 定期券を考慮した運賃計算
        fare_result = calculate_fare_with_pass(card.user_id, in_trip.station_in, req.station_code, db)

        fare = fare_result["fare"]
        current_balance = Decimal(card.user.balance or 0)

        # 残高不足チェック
        if current_balance < fare:
            return {
                "status": "error",
                "message": "insufficient_balance",
                "required_fare": float(fare),
                "current_balance": float(current_balance)
            }

        # 出場処理
        in_trip.station_out = req.station_code
        in_trip.gate_out = req.gate_code
        in_trip.exited_at = req.timestamp or datetime.utcnow()
        in_trip.status = models.TripStatus.completed
        in_trip.device_id = req.device_id
        in_trip.used_pass_id = fare_result["pass_id"]
        in_trip.fare_amount = fare
        in_trip.balance_before = current_balance
        in_trip.balance_after = current_balance - fare

        # 残高減算
        card.user.balance = current_balance - fare

        db.add(in_trip)
        db.add(card.user)
        db.commit()

        response = {
            "mode": "exit",
            "user_id": card.user_id,
            "balance": float(card.user.balance),
            "usage_amount": float(fare),
            "used_pass": fare_result["used_pass"]
        }

        if fare_result["used_pass"]:
            response["pass_type"] = fare_result["pass_type"]
            if fare_result["covered_section"]:
                response["covered_section"] = fare_result["covered_section"]
            if fare_result["charged_section"]:
                response["charged_section"] = fare_result["charged_section"]

        return response
    else:
        # create entry
        new_trip = models.Trip(
            user_id=card.user_id,
            card_id=card.id,
            station_in=req.station_code,
            gate_in=req.gate_code,
            entered_at=req.timestamp or datetime.utcnow(),
            status=models.TripStatus.in_progress,
            device_id=req.device_id,
            timestamp=req.timestamp or datetime.utcnow()
        )
        db.add(new_trip)
        db.commit()
        return {
            "mode": "entry",
            "user_id": card.user_id,
            "balance": float(card.user.balance)
        }

@app.post("/retail/purchase")
def retail_purchase(req: schemas.PurchaseRequest, db: Session = Depends(get_db)):
    """
    物販決済エンドポイント
    店員が金額を入力して、その場で決済する
    """
    print(f"\n💳 [物販決済] 金額: ¥{req.amount}")

    # カードを検索
    card = None
    if req.scan_source == "felica" and req.card_idm:
        card = db.query(models.Card).filter(models.Card.idm == req.card_idm).first()
    elif req.scan_source == "qr" and req.qr_token:
        card = db.query(models.Card).filter(models.Card.qr_token == req.qr_token).first()
    else:
        raise HTTPException(status_code=400, detail="Missing card identifier for given scan_source")

    if not card:
        return {"status": "error", "message": "card_not_registered"}

    if not card.user:
        return {"status": "error", "message": "user_not_found_for_card"}

    # 購入金額をDecimalに変換
    amount = Decimal(str(req.amount))
    current_balance = Decimal(card.user.balance or 0)

    # 残高不足チェック
    if current_balance < amount:
        return {
            "status": "error",
            "message": "insufficient_balance",
            "required_amount": float(amount),
            "current_balance": float(current_balance)
        }

    # 残高減算
    new_balance = current_balance - amount
    card.user.balance = new_balance

    # 購入記録を保存
    purchase = models.Purchase(
        user_id=card.user_id,
        card_id=card.id,
        amount=amount,
        description=req.description,
        store_code=req.store_code,
        balance_before=current_balance,
        balance_after=new_balance,
        device_id=req.device_id,
        purchased_at=req.timestamp or datetime.utcnow(),
        timestamp=req.timestamp or datetime.utcnow()
    )

    db.add(purchase)
    db.add(card.user)
    db.commit()

    print(f"   ✓ 決済完了")
    print(f"   ユーザー: {card.user.name}")
    print(f"   購入金額: ¥{amount}")
    print(f"   残高: ¥{current_balance} → ¥{new_balance}")

    return {
        "status": "success",
        "user_id": card.user_id,
        "user_name": card.user.name,
        "amount": float(amount),
        "balance_before": float(current_balance),
        "balance_after": float(new_balance),
        "purchase_id": purchase.id,
        "description": req.description
    }

# Admin / management endpoints (no auth for prototype)
@app.get("/users")
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

@app.patch("/users/{user_id}/balance")
def patch_balance(user_id: int, amount: float, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.balance = amount
    db.add(user)
    db.commit()
    return {"status": "ok", "balance": float(user.balance)}

@app.get("/trips")
def list_trips(status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(models.Trip)
    if status:
        q = q.filter(models.Trip.status == status)
    trips = q.offset(skip).limit(limit).all()
    return trips

@app.get("/trips/{trip_id}")
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="trip not found")
    return trip

@app.patch("/trips/{trip_id}/cancel")
def cancel_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="trip not found")
    trip.status = models.TripStatus.cancelled
    db.add(trip)
    db.commit()
    return {"status": "ok"}

# Purchases管理エンドポイント
@app.get("/purchases")
def list_purchases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """物販取引の一覧を取得"""
    purchases = db.query(models.Purchase).order_by(models.Purchase.purchased_at.desc()).offset(skip).limit(limit).all()
    return purchases

@app.get("/purchases/{purchase_id}")
def get_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """物販取引の詳細を取得"""
    purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="purchase not found")
    return purchase

# 顔認証エンドポイント
@app.post("/face/register")
def register_face(req: schemas.FaceRegisterRequest, db: Session = Depends(get_db)):
    """
    ユーザーの顔を登録
    """
    print(f"\n👤 [顔登録] ユーザーID: {req.user_id}")

    # ユーザーが存在するか確認
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    # 顔の特徴量を抽出
    result = face_rec.register_face(req.user_id, req.face_image_base64)

    if not result["success"]:
        return {
            "status": "error",
            "message": result["message"]
        }

    # 既存の顔データがあれば更新、なければ新規作成
    face_data = db.query(models.FaceData).filter(models.FaceData.user_id == req.user_id).first()

    embedding_json = json.dumps(result["embedding"])

    if face_data:
        # 更新
        face_data.face_encoding = embedding_json
        face_data.updated_at = datetime.utcnow()
        print(f"   ✓ 顔データを更新しました")
    else:
        # 新規作成
        face_data = models.FaceData(
            user_id=req.user_id,
            face_encoding=embedding_json,
            is_active=1
        )
        db.add(face_data)
        print(f"   ✓ 顔データを登録しました")

    db.commit()

    print(f"   ユーザー: {user.name}")
    print(f"   特徴量次元: {len(result['embedding'])}")

    return {
        "status": "success",
        "message": "顔の登録に成功しました",
        "user_id": req.user_id,
        "user_name": user.name,
        "embedding_dim": len(result["embedding"])
    }

@app.post("/face/verify")
def verify_face(req: schemas.FaceVerifyRequest, db: Session = Depends(get_db)):
    """
    顔認証を行う
    """
    print(f"\n👤 [顔認証] 認証リクエスト")

    # すべてのアクティブな顔データを取得
    face_data_list = db.query(models.FaceData).filter(models.FaceData.is_active == 1).all()

    if not face_data_list:
        return {
            "status": "error",
            "message": "登録されている顔データがありません"
        }

    print(f"   登録顔データ数: {len(face_data_list)}")

    # 各顔データと比較
    best_match = None
    best_distance = float('inf')

    for face_data in face_data_list:
        stored_embedding = json.loads(face_data.face_encoding)

        # 顔認証
        verify_result = face_rec.verify_faces(
            req.face_image_base64,
            stored_embedding,
            threshold=0.6  # Facenetの推奨閾値（調整可能）
        )

        print(f"   ユーザーID {face_data.user_id}: 距離={verify_result['distance']:.4f}, 類似度={verify_result.get('similarity', 0):.2f}%")

        if verify_result["verified"] and verify_result["distance"] < best_distance:
            best_distance = verify_result["distance"]
            best_match = {
                "user_id": face_data.user_id,
                "distance": verify_result["distance"],
                "similarity": verify_result.get("similarity", 0),
                "threshold": verify_result["threshold"]
            }

    if best_match:
        # 認証成功
        user = db.query(models.User).filter(models.User.id == best_match["user_id"]).first()

        print(f"   ✓ 認証成功: {user.name} (距離: {best_match['distance']:.4f})")

        return {
            "status": "success",
            "verified": True,
            "user_id": best_match["user_id"],
            "user_name": user.name,
            "balance": float(user.balance),
            "distance": best_match["distance"],
            "similarity": best_match["similarity"],
            "threshold": best_match["threshold"]
        }
    else:
        # 認証失敗
        print(f"   ✗ 認証失敗: 一致する顔が見つかりませんでした")

        return {
            "status": "error",
            "verified": False,
            "message": "顔認証に失敗しました"
        }

# 顔認証 - ファイルアップロード版（テスト用）
@app.post("/face/register/upload")
async def register_face_upload(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    画像ファイルをアップロードして顔を登録（テスト用）

    Args:
        user_id: ユーザーID
        file: 顔画像ファイル（JPEG/PNG）

    Returns:
        登録結果
    """
    print(f"\n📤 顔登録（ファイルアップロード）")
    print(f"   ユーザーID: {user_id}")
    print(f"   ファイル名: {file.filename}")
    print(f"   Content-Type: {file.content_type}")

    # ユーザーが存在するか確認
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {
            "status": "error",
            "message": f"ユーザーID {user_id} が見つかりません"
        }

    try:
        # ファイルを読み込んでBase64エンコード
        contents = await file.read()

        print(f"   画像サイズ: {len(contents)} bytes")
        print(f"   最初の20バイト: {contents[:20]}")

        # 画像ファイルかどうか簡易チェック
        if len(contents) == 0:
            return {
                "status": "error",
                "message": "アップロードされたファイルが空です"
            }

        # 一般的な画像ファイルのマジックナンバーチェック
        is_jpeg = contents[:2] == b'\xff\xd8'
        is_png = contents[:8] == b'\x89PNG\r\n\x1a\n'

        if not (is_jpeg or is_png):
            print(f"   ⚠️ 警告: 画像ファイルではない可能性があります")
            print(f"   ファイルヘッダー: {contents[:10].hex()}")

        base64_image = base64.b64encode(contents).decode()
        print(f"   Base64文字列長: {len(base64_image)}")

        # 既存の登録ロジックを呼び出し
        result = face_rec.register_face(user_id, base64_image)

        if not result["success"]:
            return {
                "status": "error",
                "message": result["message"]
            }

        # データベースに保存
        face_data = db.query(models.FaceData).filter(
            models.FaceData.user_id == user_id
        ).first()

        embedding_json = json.dumps(result["embedding"])

        if face_data:
            print(f"   既存の顔データを更新")
            face_data.face_encoding = embedding_json
            face_data.updated_at = datetime.utcnow()
            face_data.is_active = 1
        else:
            print(f"   新規顔データを登録")
            face_data = models.FaceData(
                user_id=user_id,
                face_encoding=embedding_json,
                is_active=1
            )
            db.add(face_data)

        db.commit()

        print(f"   ✓ 顔登録成功")

        return {
            "status": "success",
            "message": "顔の登録に成功しました",
            "user_id": user_id,
            "user_name": user.name,
            "embedding_dim": len(result["embedding"])
        }

    except Exception as e:
        print(f"   ✗ エラー: {str(e)}")
        return {
            "status": "error",
            "message": f"顔の登録に失敗: {str(e)}"
        }

@app.post("/face/verify/upload")
async def verify_face_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    画像ファイルをアップロードして顔認証（テスト用）

    Args:
        file: 顔画像ファイル（JPEG/PNG）

    Returns:
        認証結果とユーザー情報
    """
    print(f"\n🔍 顔認証（ファイルアップロード）")
    print(f"   ファイル名: {file.filename}")
    print(f"   Content-Type: {file.content_type}")

    try:
        # ファイルを読み込んでBase64エンコード
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode()

        print(f"   画像サイズ: {len(contents)} bytes")

        # データベースから全ての有効な顔データを取得
        face_data_list = db.query(models.FaceData).filter(
            models.FaceData.is_active == 1
        ).all()

        if not face_data_list:
            print(f"   ✗ 登録された顔データがありません")
            return {
                "status": "error",
                "verified": False,
                "message": "登録された顔データがありません"
            }

        print(f"   登録ユーザー数: {len(face_data_list)}")

        # 各ユーザーの顔と比較
        best_match = None
        best_distance = float('inf')

        for face_data in face_data_list:
            stored_embedding = json.loads(face_data.face_encoding)

            # 顔認証を実行
            verify_result = face_rec.verify_faces(
                base64_image,
                stored_embedding,
                threshold=0.6  # Facenetの推奨閾値
            )

            print(f"   ユーザーID {face_data.user_id}: 距離={verify_result['distance']:.4f}, 認証={'成功' if verify_result['verified'] else '失敗'}")

            # 認証成功かつ最も距離が近い場合
            if verify_result["verified"] and verify_result["distance"] < best_distance:
                best_distance = verify_result["distance"]
                best_match = {
                    "user_id": face_data.user_id,
                    "distance": verify_result["distance"],
                    "similarity": verify_result["similarity"],
                    "threshold": verify_result["threshold"]
                }

        # 最も一致したユーザーがいる場合
        if best_match:
            user = db.query(models.User).filter(
                models.User.id == best_match["user_id"]
            ).first()

            print(f"   ✓ 認証成功: {user.name} (ID: {user.id})")

            return {
                "status": "success",
                "verified": True,
                "user_id": best_match["user_id"],
                "user_name": user.name,
                "balance": float(user.balance),
                "distance": best_match["distance"],
                "similarity": best_match["similarity"],
                "threshold": best_match["threshold"]
            }

        print(f"   ✗ 認証失敗: 一致する顔が見つかりませんでした")

        return {
            "status": "error",
            "verified": False,
            "message": "顔認証に失敗しました"
        }

    except Exception as e:
        print(f"   ✗ エラー: {str(e)}")
        return {
            "status": "error",
            "verified": False,
            "message": f"顔認証に失敗: {str(e)}"
        }

# Cards管理エンドポイント
@app.get("/cards")
def list_cards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cards = db.query(models.Card).offset(skip).limit(limit).all()
    return cards

@app.get("/cards/{card_id}")
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    return card

# ユーザー登録エンドポイント
@app.post("/register")
def register_user(name: str, email: Optional[str] = None, initial_balance: float = 1000, db: Session = Depends(get_db)):
    """
    新規ユーザーを登録し、QRカードを発行する
    """
    import secrets

    # 新しいユーザーを作成
    new_user = models.User(
        name=name,
        email=email,
        balance=initial_balance
    )
    db.add(new_user)
    db.flush()  # IDを取得するためにflush

    # ユニークなQRトークンを生成
    qr_token = f"QR_{secrets.token_hex(8).upper()}"

    # ユーザーテーブルにもQRトークンを保存
    new_user.qr_token = qr_token

    # QRカードを作成
    new_card = models.Card(
        user_id=new_user.id,
        qr_token=qr_token,
        label=f"{name}のQRカード"
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_card)

    return {
        "status": "ok",
        "id": new_user.id,
        "user_id": new_user.id,
        "name": new_user.name,
        "balance": float(new_user.balance),
        "qr_token": qr_token,
        "card_id": new_card.id
    }

# Stations管理エンドポイント
@app.get("/stations")
def list_stations(db: Session = Depends(get_db)):
    stations = db.query(models.Station).all()
    return stations

# Gates管理エンドポイント
@app.get("/gates")
def list_gates(db: Session = Depends(get_db)):
    gates = db.query(models.Gate).all()
    return gates

# ログインエンドポイント
@app.post("/login")
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    QRトークンでログイン
    """
    user = db.query(models.User).filter(models.User.qr_token == req.qr_token).first()
    if not user:
        return {
            "status": "error",
            "message": "ユーザーが見つかりません"
        }

    return {
        "status": "ok",
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "balance": float(user.balance),
        "qr_token": user.qr_token,
        "card_idm": user.card_idm
    }

# 残高取得エンドポイント
@app.get("/users/{user_id}/balance")
def get_user_balance(user_id: int, db: Session = Depends(get_db)):
    """
    ユーザーの残高を取得
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    return {
        "balance": float(user.balance)
    }

# チャージエンドポイント
@app.post("/charge")
def charge(req: schemas.ChargeRequest, db: Session = Depends(get_db)):
    """
    ユーザーの残高にチャージ
    """
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    user.balance = Decimal(user.balance or 0) + Decimal(req.amount)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "status": "ok",
        "balance": float(user.balance),
        "message": f"¥{req.amount:.0f}をチャージしました"
    }

# カードIDm紐付けエンドポイント
@app.post("/link_card")
def link_card(req: schemas.LinkCardRequest, db: Session = Depends(get_db)):
    """
    QRトークンにFeliCa IDmを紐付ける
    """
    # ユーザーテーブルのcard_idmを更新
    user = db.query(models.User).filter(models.User.qr_token == req.qr_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    user.card_idm = req.card_idm

    # カードテーブルも更新
    card = db.query(models.Card).filter(models.Card.qr_token == req.qr_token).first()
    if card:
        card.idm = req.card_idm
        db.add(card)

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "status": "ok",
        "message": "カードIDmを紐付けました",
        "card_idm": req.card_idm
    }

# 定期券管理エンドポイント
@app.post("/passes")
def create_pass(req: schemas.PassCreateRequest, db: Session = Depends(get_db)):
    """
    定期券を新規作成
    """
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    new_pass = models.Pass(
        user_id=req.user_id,
        pass_type=req.pass_type,
        station_from=req.station_from,
        station_to=req.station_to,
        valid_from=req.valid_from,
        valid_until=req.valid_until,
        is_active=1
    )
    db.add(new_pass)
    db.commit()
    db.refresh(new_pass)

    return {
        "status": "ok",
        "pass_id": new_pass.id,
        "message": "定期券を作成しました"
    }

@app.get("/passes")
def list_passes(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    定期券一覧を取得
    """
    query = db.query(models.Pass)
    if user_id:
        query = query.filter(models.Pass.user_id == user_id)

    passes = query.offset(skip).limit(limit).all()
    return passes

@app.get("/passes/{pass_id}")
def get_pass(pass_id: int, db: Session = Depends(get_db)):
    """
    定期券詳細を取得
    """
    pass_obj = db.query(models.Pass).filter(models.Pass.id == pass_id).first()
    if not pass_obj:
        raise HTTPException(status_code=404, detail="pass not found")
    return pass_obj

@app.patch("/passes/{pass_id}/deactivate")
def deactivate_pass(pass_id: int, db: Session = Depends(get_db)):
    """
    定期券を無効化
    """
    pass_obj = db.query(models.Pass).filter(models.Pass.id == pass_id).first()
    if not pass_obj:
        raise HTTPException(status_code=404, detail="pass not found")

    pass_obj.is_active = 0
    db.add(pass_obj)
    db.commit()
    return {"status": "ok", "message": "定期券を無効化しました"}

@app.get("/users/{user_id}/passes")
def get_user_passes(user_id: int, active_only: bool = True, db: Session = Depends(get_db)):
    """
    ユーザーの定期券一覧を取得
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    query = db.query(models.Pass).filter(models.Pass.user_id == user_id)

    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            models.Pass.is_active == 1,
            models.Pass.valid_from <= now,
            models.Pass.valid_until >= now
        )

    passes = query.all()
    return passes

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    ユーザーを削除
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"status": "error", "message": "ユーザーが見つかりません"}

    # カード、定期券、トリップも削除される（CASCADE設定による）
    db.delete(user)
    db.commit()
    return {"status": "ok", "message": "ユーザーを削除しました"}

@app.delete("/passes/{pass_id}")
def delete_pass(pass_id: int, db: Session = Depends(get_db)):
    """
    定期券を削除
    """
    pass_obj = db.query(models.Pass).filter(models.Pass.id == pass_id).first()
    if not pass_obj:
        return {"status": "error", "message": "定期券が見つかりません"}

    db.delete(pass_obj)
    db.commit()
    return {"status": "ok", "message": "定期券を削除しました"}
