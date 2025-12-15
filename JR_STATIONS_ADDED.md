# JR線駅データ追加完了

## 実施日時
2025年12月14日

## 概要
FeliCa Gate Systemに実在のJR線駅データを追加しました。

---

## 追加した路線と駅

### 1. 京浜東北線（東京〜大船）- 26駅

| 駅コード | 駅名 |
|---------|------|
| JK01 | 東京 |
| JK02 | 有楽町 |
| JK03 | 新橋 |
| JK04 | 浜松町 |
| JK05 | 田町 |
| JK06 | 高輪ゲートウェイ |
| JK07 | 品川 |
| JK08 | 大井町 |
| JK09 | 大森 |
| JK10 | 蒲田 |
| JK11 | 川崎 |
| JK12 | 鶴見 |
| JK13 | 新子安 |
| JK14 | 東神奈川 |
| JK15 | 横浜 |
| JK16 | 桜木町 |
| JK17 | 関内 |
| JK18 | 石川町 |
| JK19 | 山手 |
| JK20 | 根岸 |
| JK21 | 磯子 |
| JK22 | 新杉田 |
| JK23 | 洋光台 |
| JK24 | 港南台 |
| JK25 | 本郷台 |
| JK26 | 大船 |

### 2. 横須賀線（品川〜大船）- 9駅

| 駅コード | 駅名 |
|---------|------|
| JO01 | 品川 |
| JO02 | 西大井 |
| JO03 | 武蔵小杉 |
| JO04 | 新川崎 |
| JO05 | 横浜 |
| JO06 | 保土ケ谷 |
| JO07 | 東戸塚 |
| JO08 | 戸塚 |
| JO09 | 大船 |

### 3. 南武線（立川〜川崎）- 20駅

| 駅コード | 駅名 |
|---------|------|
| JN01 | 武蔵小杉 |
| JN02 | 武蔵中原 |
| JN03 | 武蔵新城 |
| JN04 | 武蔵溝ノ口 |
| JN05 | 津田山 |
| JN06 | 久地 |
| JN07 | 宿河原 |
| JN08 | 登戸 |
| JN09 | 中野島 |
| JN10 | 稲田堤 |
| JN11 | 矢野口 |
| JN12 | 稲城長沼 |
| JN13 | 南多摩 |
| JN14 | 府中本町 |
| JN15 | 分倍河原 |
| JN16 | 谷保 |
| JN17 | 矢川 |
| JN18 | 西国立 |
| JN19 | 立川 |
| JN20 | 川崎 |

---

## 追加サマリー

### 駅データ
- **追加駅数**: 55駅
- **既存駅数**: 3駅（ST01:東京駅, ST02:新宿駅, ST03:渋谷駅）
- **合計駅数**: 58駅

### ゲートデータ
- **追加ゲート数**: 110個（各駅に入口・出口の2つ）
- **既存ゲート数**: 5個
- **合計ゲート数**: 115個

### 駅コード体系
- **JK**: 京浜東北線（Keihin-Tohoku Line）
- **JO**: 横須賀線（Yokosuka Line）
- **JN**: 南武線（Nambu Line）

---

## 実装ファイル

### 1. add_jr_stations.py
駅データを追加するスクリプト

**実行方法:**
```bash
cd server
python add_jr_stations.py
```

**機能:**
- 55駅のデータを stations テーブルに追加
- 既存の駅コードはスキップ
- 追加結果をコンソールに表示

### 2. add_jr_gates.py
各駅にゲートを追加するスクリプト

**実行方法:**
```bash
cd server
python add_jr_gates.py
```

**機能:**
- 各駅に入口（_IN）と出口（_OUT）のゲートを追加
- 既存のゲートコードはスキップ
- 追加結果をコンソールに表示

---

## ゲート命名規則

各駅に以下の2つのゲートが追加されます：

```
{駅コード}_IN  - 入口ゲート
{駅コード}_OUT - 出口ゲート
```

**例:**
- JK01_IN - 東京 入口
- JK01_OUT - 東京 出口
- JK15_IN - 横浜 入口
- JK15_OUT - 横浜 出口

---

## 使用例

### 1. 定期券の作成（横浜〜川崎）

```bash
curl -X POST "http://localhost:8000/passes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "JK15",
    "station_to": "JK11",
    "valid_from": "2025-12-01T00:00:00Z",
    "valid_until": "2026-02-28T23:59:59Z"
  }'
```

### 2. 入場テスト（東京駅）

```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_source": "qr",
    "qr_token": "QR_SUZUKI_001",
    "station_code": "JK01",
    "gate_code": "JK01_IN",
    "timestamp": "2025-12-14T09:00:00Z",
    "device_id": "gate-tokyo-01"
  }'
```

### 3. 出場テスト（横浜駅）

```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_source": "qr",
    "qr_token": "QR_SUZUKI_001",
    "station_code": "JK15",
    "gate_code": "JK15_OUT",
    "timestamp": "2025-12-14T09:30:00Z",
    "device_id": "gate-yokohama-01"
  }'
```

---

## 運賃計算

現在の運賃計算ロジック:
```
運賃 = BASE_FARE (¥150) + 駅間距離 × FARE_PER_STATION (¥50)
```

**例:**
- 東京（JK01）→ 横浜（JK15）: 14駅
  - 運賃 = ¥150 + 14 × ¥50 = **¥850**

- 武蔵小杉（JN01）→ 川崎（JN20）: 19駅
  - 運賃 = ¥150 + 19 × ¥50 = **¥1,100**

※実際の運賃とは異なる簡易計算です

---

## 管理画面での確認

### 駅一覧
管理画面（admin/index.html）の「🏢 駅・ゲート」セクションで確認できます。

### 定期券作成
「🎫 定期券管理」セクションで、新しい駅コードを使用して定期券を作成できます。

### 駅選択ドロップダウン
定期券作成フォームの駅選択ドロップダウンに、すべての駅が表示されます。

---

## データベーススキーマ

### stations テーブル
```sql
CREATE TABLE stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT
);
```

### gates テーブル
```sql
CREATE TABLE gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    station_id INTEGER,
    name TEXT,
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

---

## 確認コマンド

### 駅数の確認
```bash
sqlite3 server/felica_gate.db "SELECT COUNT(*) FROM stations;"
# → 58
```

### ゲート数の確認
```bash
sqlite3 server/felica_gate.db "SELECT COUNT(*) FROM gates;"
# → 115
```

### 京浜東北線の駅一覧
```bash
sqlite3 server/felica_gate.db "SELECT code, name FROM stations WHERE code LIKE 'JK%' ORDER BY code;"
```

### 横須賀線の駅一覧
```bash
sqlite3 server/felica_gate.db "SELECT code, name FROM stations WHERE code LIKE 'JO%' ORDER BY code;"
```

### 南武線の駅一覧
```bash
sqlite3 server/felica_gate.db "SELECT code, name FROM stations WHERE code LIKE 'JN%' ORDER BY code;"
```

### 特定駅のゲート確認
```bash
sqlite3 server/felica_gate.db "SELECT g.code, g.name FROM gates g JOIN stations s ON g.station_id = s.id WHERE s.code = 'JK15';"
# → 横浜駅のゲート一覧
```

---

## 今後の拡張

### 追加可能な路線
- 山手線
- 中央線
- 総武線
- 東海道線
- 常磐線
- など

### 改善案
- 駅間の実際の距離データを追加
- 実際の運賃データを追加
- 路線情報テーブルの追加
- 乗り換え情報の追加

---

## トラブルシューティング

### 問題: 駅が重複している
**原因**: スクリプトを複数回実行した
**対処**: スクリプトは重複チェックを行うため、再実行しても問題ありません

### 問題: ゲートが表示されない
**原因**: add_jr_gates.py を実行していない
**対処**: `python add_jr_gates.py` を実行してください

### 問題: 管理画面で駅が表示されない
**原因**: ブラウザキャッシュ
**対処**: ブラウザのハードリフレッシュ（Ctrl+Shift+R または Cmd+Shift+R）

---

## まとめ

✅ **55駅を追加**
- 京浜東北線: 26駅
- 横須賀線: 9駅
- 南武線: 20駅

✅ **110ゲートを追加**
- 各駅に入口・出口の2つ

✅ **合計**
- 駅: 58駅
- ゲート: 115個

✅ **実用的な駅データ**
- 実在のJR線駅名
- 路線別の駅コード体系
- 定期券・改札機能で使用可能

これにより、FeliCa Gate Systemで実際の路線を使ったリアルなテストが可能になりました！

---

**実装者**: Claude Sonnet 4.5
**完了日**: 2025年12月14日
