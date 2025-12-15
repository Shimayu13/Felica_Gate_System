# ユーザーアプリ: 営業距離ベース運賃システム対応ガイド

## 概要

このドキュメントは、ユーザーアプリを新しい営業距離ベースの運賃計算システムに対応させるための手順を説明します。

## 背景

2025年12月14日に、Felica Gate Systemの運賃計算方式を以下のように変更しました:

**変更前**: 駅数ベースの簡易計算（BASE_FARE + 駅数 × FARE_PER_STATION）
**変更後**: 実際のJR東日本の営業距離に基づく運賃計算

## システム変更の影響

### 1. データベース構造の変更

#### 新規テーブル

**station_routes**: 駅と路線の関係
```sql
CREATE TABLE station_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id INTEGER NOT NULL,
    line TEXT NOT NULL,
    sub_line TEXT NOT NULL,
    distance_from_origin REAL NOT NULL,
    FOREIGN KEY (station_id) REFERENCES stations(id)
)
```

**fare_table**: 営業キロと運賃の対応表
```sql
CREATE TABLE fare_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    min_distance_km REAL NOT NULL UNIQUE,
    fare INTEGER NOT NULL
)
```

#### 駅データの変更

**駅数**: 58駅 → 281駅
**ゲート数**: 115個 → 562個

**駅コードの変更**:
- 旧: `JK01`, `JK02`, `ST01` など
- 新: `STATION_1`, `STATION_2`, `STATION_3` など

### 2. API変更

#### `/scan` エンドポイント

**リクエスト**: 変更なし
```json
{
  "scan_source": "qr",
  "qr_token": "QR_xxxxx",
  "station_code": "STATION_1",
  "gate_code": "STATION_1_IN",
  "timestamp": "2025-12-14T10:00:00Z",
  "device_id": "xxxxx"
}
```

**レスポンス**: 変更なし（運賃計算ロジックのみ変更）
```json
{
  "mode": "exit",
  "user_id": 1,
  "balance": 9472.0,
  "usage_amount": 528.0,
  "used_pass": false
}
```

**運賃計算の違い**:
- 旧: 東京(JK01) → 横浜(JK15): `150 + (15-1) × 50 = ¥850`
- 新: 東京(STATION_1) → 横浜(STATION_15): 営業キロ 28.8km → `¥528`（実際のJR運賃）

#### `/stations` エンドポイント

**変更**: 駅数が増加、駅コードが変更

**レスポンス例**:
```json
[
  {
    "id": 1,
    "code": "STATION_1",
    "name": "東京"
  },
  {
    "id": 2,
    "code": "STATION_2",
    "name": "有楽町"
  }
]
```

#### `/gates` エンドポイント

**変更**: ゲート数が増加、ゲートコードが変更

**レスポンス例**:
```json
[
  {
    "id": 1,
    "code": "STATION_1_IN",
    "station_id": 1,
    "name": "東京 入口"
  },
  {
    "id": 2,
    "code": "STATION_1_OUT",
    "station_id": 1,
    "name": "東京 出口"
  }
]
```

### 3. 定期券（Pass）システムへの影響

定期券の駅コードも変更されました:

**変更前**:
```json
{
  "station_from": "JK01",
  "station_to": "JK15"
}
```

**変更後**:
```json
{
  "station_from": "STATION_1",
  "station_to": "STATION_15"
}
```

## ユーザーアプリで必要な対応

### 必須対応

#### 1. データ取得の更新

ユーザーアプリでは、サーバーから最新の駅・ゲート情報を取得して表示する必要があります。

**既存の実装確認**:
```swift
// User_App の実装を確認
// 駅やゲートのリストを表示している箇所
```

**対応方法**:
- `/stations` エンドポイントから駅情報を取得
- 駅コードが `STATION_XXX` 形式に変わっていることを考慮
- 既存の保存済み設定（旧駅コード）をクリアまたは移行

#### 2. 運賃表示の更新

ユーザーアプリで運賃を表示している場合、以下を更新:

**例: トリップ履歴の運賃表示**
```swift
// 旧: 簡易計算ロジックをクライアント側で実装していた場合
let fare = baseFare + (stationDiff * farePerStation)

// 新: サーバーから返される fare_amount を使用
let fare = trip.fare_amount  // サーバー側で正確に計算された運賃
```

#### 3. 定期券機能の更新（該当する場合）

ユーザーアプリで定期券の作成・表示機能がある場合:

**駅選択UI**:
- 旧駅コード（`JK01` など）から新駅コード（`STATION_1`）への移行
- サーバーから取得した駅リストを使用

**定期券の有効性表示**:
- 既存の定期券は旧駅コードを使用している可能性がある
- サーバー側で処理されるため、ユーザーアプリ側の変更は不要

### 推奨対応

#### 1. 運賃シミュレーション機能

ユーザーが区間を選択して運賃を確認できる機能を追加:

**新規API追加（サーバー側）**:
```python
@app.get("/fare/calculate")
def calculate_fare_api(
    station_from: str,
    station_to: str,
    db: Session = Depends(get_db)
):
    """
    2駅間の運賃を計算して返す
    """
    fare = calculate_fare(station_from, station_to, db)
    distance = calculate_station_distance(station_from, station_to, db)

    return {
        "station_from": station_from,
        "station_to": station_to,
        "distance_km": distance,
        "fare": float(fare)
    }
```

**ユーザーアプリ側の実装例**:
```swift
struct FareCalculatorView: View {
    @State private var fromStation: Station?
    @State private var toStation: Station?
    @State private var fareResult: FareResult?

    var body: some View {
        VStack {
            // 駅選択
            Picker("出発駅", selection: $fromStation) {
                ForEach(stations) { station in
                    Text(station.name).tag(station as Station?)
                }
            }

            Picker("到着駅", selection: $toStation) {
                ForEach(stations) { station in
                    Text(station.name).tag(station as Station?)
                }
            }

            // 運賃表示
            if let result = fareResult {
                VStack {
                    Text("営業キロ: \(String(format: "%.1f", result.distance))km")
                    Text("運賃: ¥\(result.fare)")
                        .font(.largeTitle)
                }
            }

            Button("運賃を計算") {
                calculateFare()
            }
        }
    }

    func calculateFare() {
        guard let from = fromStation, let to = toStation else { return }

        apiClient.calculateFare(from: from.code, to: to.code) { result in
            // 結果を表示
        }
    }
}
```

#### 2. 路線図の表示

281駅の路線図を表示する機能:

**データ取得**:
- `/stations` から全駅を取得
- 新規エンドポイント `/station-routes` から路線情報を取得

**表示方法**:
- リスト表示（路線ごとにグループ化）
- 地図表示（実際の駅位置を表示）

#### 3. トリップ履歴の詳細表示

営業距離や使用路線を表示:

**新規APIレスポンスフィールド（将来の拡張）**:
```json
{
  "trip_id": 123,
  "station_in": "STATION_1",
  "station_out": "STATION_15",
  "fare_amount": 528,
  "distance_km": 28.8,
  "route_used": "東海道線 本線"
}
```

## 移行手順

### ステップ1: サーバーAPI確認

```bash
# サーバーが稼働していることを確認
curl http://localhost:8000/stations | jq

# 駅数が281、駅コードがSTATION_XXであることを確認
```

### ステップ2: ユーザーアプリのコード確認

```bash
# User_App ディレクトリで駅コードの使用箇所を検索
cd User_App
grep -r "JK01" .
grep -r "ST01" .

# @AppStorage で保存されている設定値を確認
grep -r "@AppStorage.*station" .
```

### ステップ3: ハードコードされた駅コードの更新

**変更例**:
```swift
// 旧
@AppStorage("default_station") private var defaultStation = "JK01"

// 新
@AppStorage("default_station") private var defaultStation = "STATION_1"
```

### ステップ4: 駅・ゲート情報の動的取得

**変更前（ハードコード）**:
```swift
let stations = ["JK01": "東京", "JK02": "有楽町", ...]
```

**変更後（APIから取得）**:
```swift
@State private var stations: [Station] = []

func loadStations() {
    apiClient.getStations { result in
        switch result {
        case .success(let data):
            self.stations = try! JSONDecoder().decode([Station].self, from: data)
        case .failure(let error):
            print("駅情報の取得に失敗: \(error)")
        }
    }
}
```

### ステップ5: 定期券データの確認

既存の定期券データが旧駅コードを使用している場合:

**データベースマイグレーション（サーバー側）**:
```python
# 必要に応じて既存の定期券の駅コードを更新
# 例: JK01 → STATION_1 のマッピング

STATION_CODE_MIGRATION = {
    "JK01": "STATION_1",
    "JK02": "STATION_2",
    # ...
}

# マイグレーションスクリプトを実行
```

**ユーザーアプリ側**:
- 定期券情報はサーバーから取得するため、クライアント側の変更は不要
- 表示時に駅名を `/stations` APIから取得して表示

### ステップ6: テスト

1. **ユーザー登録**: 新規ユーザーを作成し、QRコードが生成されることを確認
2. **残高確認**: ユーザーの残高が正しく表示されることを確認
3. **駅情報表示**: 281駅が正しく表示されることを確認
4. **定期券表示**: 既存の定期券（ある場合）が正しく表示されることを確認
5. **運賃計算**: 新しい運賃計算ロジックが反映されることを確認（トリップ履歴など）

## トラブルシューティング

### 問題1: 駅情報が表示されない

**原因**: サーバーAPIが稼働していない、またはエンドポイントが変更された

**解決方法**:
```bash
# サーバーの起動を確認
cd server
python3 run.py

# エンドポイントを確認
curl http://localhost:8000/stations
```

### 問題2: 旧駅コードが残っている

**原因**: @AppStorageやUserDefaultsに保存された旧設定

**解決方法**:
```swift
// アプリ起動時に旧設定をクリア
func migrateOldStationCodes() {
    let oldCodes = ["JK01", "JK02", "JK03", "ST01", "ST02", "ST03"]

    if oldCodes.contains(UserDefaults.standard.string(forKey: "station_code") ?? "") {
        // 旧駅コードが保存されている場合は削除
        UserDefaults.standard.removeObject(forKey: "station_code")
        UserDefaults.standard.removeObject(forKey: "gate_code")
    }
}
```

### 問題3: 運賃が正しく表示されない

**原因**: クライアント側で独自に運賃計算をしている

**解決方法**:
- サーバーから返される `fare_amount` を使用
- クライアント側での運賃計算ロジックを削除

```swift
// 旧: クライアント側で計算
let fare = calculateFareLocally(from: station1, to: station2)

// 新: サーバーから取得
let fare = trip.fare_amount  // サーバーレスポンスから取得
```

## 参考情報

### 関連ドキュメント

- [DISTANCE_BASED_FARE_SYSTEM.md](DISTANCE_BASED_FARE_SYSTEM.md) - 営業距離ベース運賃システムの詳細
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API仕様書
- [PASS_DOCUMENTATION.md](PASS_DOCUMENTATION.md) - 定期券システムの仕様

### データファイル

- `server/営業距離データ.csv` - 駅の営業キロデータ（281駅、327ルート）
- `server/運賃体系.csv` - JR東日本の運賃テーブル（38段階）

### テストデータ

テスト用のユーザーを作成:
```bash
cd server
python3 test_end_to_end.py
```

## まとめ

ユーザーアプリの主な対応ポイント:

✅ **必須対応**:
1. ハードコードされた駅コードを削除
2. `/stations` APIから駅情報を動的に取得
3. サーバーから返される運賃を使用（クライアント側計算を削除）

✅ **推奨対応**:
1. 運賃シミュレーション機能の追加
2. 路線図の表示
3. トリップ履歴の詳細表示（営業キロ、路線名など）

✅ **テスト**:
1. 新規ユーザー登録
2. 駅情報の表示
3. 運賃計算の確認

---

**作成日**: 2025年12月14日
**対象バージョン**: 営業距離ベース運賃システム v1.0
