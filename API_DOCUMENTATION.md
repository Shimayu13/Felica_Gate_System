# FeliCa Gate System API ドキュメント

## ユーザーアプリ向けAPIエンドポイント

### 1. ログイン
**エンドポイント:** `POST /login`

**説明:** QRトークンを使用してユーザー情報を取得します。

**リクエストボディ:**
```json
{
  "qr_token": "QR_SUZUKI_001"
}
```

**成功レスポンス:**
```json
{
  "status": "ok",
  "id": 3,
  "name": "鈴木一郎",
  "email": "suzuki@example.com",
  "balance": 10000.0,
  "qr_token": "QR_SUZUKI_001",
  "card_idm": null
}
```

**エラーレスポンス:**
```json
{
  "status": "error",
  "message": "ユーザーが見つかりません"
}
```

**実装方法:**
```swift
// Swiftでの使用例
struct LoginRequest: Codable {
    let qr_token: String
}

struct LoginResponse: Codable {
    let status: String
    let id: Int?
    let name: String?
    let email: String?
    let balance: Double?
    let qr_token: String?
    let card_idm: String?
    let message: String?
}

func login(qrToken: String, completion: @escaping (Result<LoginResponse, Error>) -> Void) {
    let url = URL(string: "http://localhost:8000/login")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let body = LoginRequest(qr_token: qrToken)
    request.httpBody = try? JSONEncoder().encode(body)

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(.failure(error))
            return
        }

        guard let data = data else { return }

        if let loginResponse = try? JSONDecoder().decode(LoginResponse.self, from: data) {
            completion(.success(loginResponse))
        }
    }.resume()
}
```

---

### 2. 残高取得
**エンドポイント:** `GET /users/{user_id}/balance`

**説明:** 指定したユーザーの残高を取得します。

**パラメータ:**
- `user_id` (パスパラメータ): ユーザーID

**レスポンス:**
```json
{
  "balance": 10000.0
}
```

**エラーレスポンス:**
- `404`: ユーザーが見つかりません

---

### 3. チャージ
**エンドポイント:** `POST /charge`

**説明:** ユーザーの残高にチャージします。

**リクエストボディ:**
```json
{
  "user_id": 3,
  "amount": 1000
}
```

**レスポンス:**
```json
{
  "status": "ok",
  "balance": 11000.0,
  "message": "¥1000をチャージしました"
}
```

**エラーレスポンス:**
- `404`: ユーザーが見つかりません
- `400`: チャージ金額は正の値である必要があります

---

### 4. ユーザー登録
**エンドポイント:** `POST /register`

**説明:** 新規ユーザーを登録し、QRカードを発行します。

**クエリパラメータ:**
- `name` (必須): ユーザー名
- `email` (オプション): メールアドレス
- `initial_balance` (オプション, デフォルト=1000): 初期残高

**例:**
```
POST /register?name=山田太郎&email=yamada@example.com&initial_balance=5000
```

**レスポンス:**
```json
{
  "status": "ok",
  "id": 9,
  "user_id": 9,
  "name": "山田太郎",
  "balance": 5000.0,
  "qr_token": "QR_661303335D0445A6",
  "card_id": 9
}
```

---

### 5. カードIDm紐付け
**エンドポイント:** `POST /link_card`

**説明:** QRトークンにFeliCa IDmを紐付けます。

**リクエストボディ:**
```json
{
  "qr_token": "QR_SUZUKI_001",
  "card_idm": "ABCD1234567890EF"
}
```

**レスポンス:**
```json
{
  "status": "ok",
  "message": "カードIDmを紐付けました",
  "card_idm": "ABCD1234567890EF"
}
```

**エラーレスポンス:**
- `404`: ユーザーが見つかりません

---

## 改札機アプリ向けAPIエンドポイント

### 6. スキャン（入退場記録）
**エンドポイント:** `POST /scan`

**説明:** QRコードまたはFeliCaカードをスキャンし、入退場記録を作成します。

**リクエストボディ:**
```json
{
  "scan_source": "qr",
  "qr_token": "QR_SUZUKI_001",
  "station_code": "ST01",
  "gate_code": "A1",
  "timestamp": "2025-12-14T10:30:00Z",
  "device_id": "device-001"
}
```

**レスポンス（入場）:**
```json
{
  "mode": "entry",
  "user_id": 3,
  "balance": 10000.0
}
```

**レスポンス（出場）:**
```json
{
  "mode": "exit",
  "user_id": 3,
  "balance": 9850.0,
  "usage_amount": 150.0
}
```

**エラーレスポンス（残高不足）:**
```json
{
  "status": "error",
  "message": "insufficient_balance",
  "required_fare": 200.0,
  "current_balance": 100.0
}
```

**その他のエラー:**
- `card_not_registered`: カードが登録されていません
- `user_not_found_for_card`: カードにユーザーが紐付いていません

---

## 管理アプリ向けAPIエンドポイント

### 7. ユーザー一覧
**エンドポイント:** `GET /users`

**パラメータ:**
- `skip` (オプション, デフォルト=0): スキップ件数
- `limit` (オプション, デフォルト=100): 取得件数

**レスポンス:**
```json
[
  {
    "id": 1,
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "balance": 5000.0,
    "qr_token": "QR_TANAKA_001",
    "card_idm": "0123456789ABCDEF"
  }
]
```

---

### 8. ユーザー詳細
**エンドポイント:** `GET /users/{user_id}`

**レスポンス:**
```json
{
  "id": 1,
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "balance": 5000.0,
  "qr_token": "QR_TANAKA_001",
  "card_idm": "0123456789ABCDEF"
}
```

---

### 9. 残高調整
**エンドポイント:** `PATCH /users/{user_id}/balance`

**パラメータ:**
- `amount` (クエリパラメータ): 新しい残高

**例:**
```
PATCH /users/3/balance?amount=15000
```

**レスポンス:**
```json
{
  "status": "ok",
  "balance": 15000.0
}
```

---

### 10. 入退場記録一覧
**エンドポイント:** `GET /trips`

**パラメータ:**
- `status` (オプション): ステータスでフィルタ (in_progress, completed, cancelled)
- `skip` (オプション, デフォルト=0): スキップ件数
- `limit` (オプション, デフォルト=100): 取得件数

**レスポンス:**
```json
[
  {
    "id": 1,
    "user_id": 3,
    "card_id": 3,
    "station_in": "ST01",
    "gate_in": "A1",
    "station_out": "ST02",
    "gate_out": "B1",
    "status": "completed",
    "entered_at": "2025-12-14T10:00:00Z",
    "exited_at": "2025-12-14T10:30:00Z",
    "device_id": "device-001"
  }
]
```

---

### 11. トリップキャンセル
**エンドポイント:** `PATCH /trips/{trip_id}/cancel`

**レスポンス:**
```json
{
  "status": "ok"
}
```

---

### 12. カード一覧
**エンドポイント:** `GET /cards`

**レスポンス:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "idm": "0123456789ABCDEF",
    "qr_token": "QR_TANAKA_001",
    "label": "田中さんのFeliCa"
  }
]
```

---

### 13. 駅一覧
**エンドポイント:** `GET /stations`

**レスポンス:**
```json
[
  {
    "id": 1,
    "code": "ST01",
    "name": "東京駅"
  }
]
```

---

### 14. ゲート一覧
**エンドポイント:** `GET /gates`

**レスポンス:**
```json
[
  {
    "id": 1,
    "code": "A1",
    "station_id": 1,
    "name": "東京駅A1改札"
  }
]
```

---

## データベーススキーマ

### usersテーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| name | TEXT | ユーザー名 |
| email | TEXT | メールアドレス（UNIQUE） |
| balance | NUMERIC(10,2) | 残高 |
| qr_token | TEXT | QRトークン（UNIQUE、INDEX付き） |
| card_idm | TEXT | FeliCa IDm |

### cardsテーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| user_id | INTEGER | ユーザーID（外部キー） |
| idm | TEXT | FeliCa IDm（UNIQUE） |
| qr_token | TEXT | QRトークン（UNIQUE） |
| label | TEXT | カードラベル |

### tripsテーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| user_id | INTEGER | ユーザーID（外部キー） |
| card_id | INTEGER | カードID（外部キー） |
| station_in | TEXT | 入場駅コード |
| gate_in | TEXT | 入場ゲートコード |
| station_out | TEXT | 出場駅コード |
| gate_out | TEXT | 出場ゲートコード |
| status | ENUM | ステータス（in_progress, completed, cancelled） |
| entered_at | DATETIME | 入場時刻 |
| exited_at | DATETIME | 出場時刻 |
| device_id | TEXT | デバイスID |
| timestamp | DATETIME | タイムスタンプ |

### stationsテーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| code | TEXT | 駅コード（UNIQUE） |
| name | TEXT | 駅名 |

### gatesテーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| code | TEXT | ゲートコード（UNIQUE） |
| station_id | INTEGER | 駅ID（外部キー） |
| name | TEXT | ゲート名 |

---

## 運賃計算

運賃は駅コードに含まれる数字の差分を距離とみなして計算されます。

**計算式:**
```
運賃 = BASE_FARE + (駅間距離 × FARE_PER_STATION)
     = 150円 + (|入場駅番号 - 出場駅番号| × 50円)
```

**例:**
- ST01 → ST02: 150 + (|1-2| × 50) = 200円
- ST01 → ST03: 150 + (|1-3| × 50) = 250円

---

## テスト用データ

マイグレーション後、以下のテストユーザーが利用可能です：

| ID | 名前 | QRトークン | 残高 | カードIDm |
|----|------|-----------|------|----------|
| 1 | 田中太郎 | QR_TANAKA_001 | ¥5,000 | 0123456789ABCDEF |
| 2 | 佐藤花子 | QR_SATO_001 | ¥3,000 | FEDCBA9876543210 |
| 3 | 鈴木一郎 | QR_SUZUKI_001 | ¥10,000 | null |

---

## セットアップ手順

1. **マイグレーションスクリプトの実行:**
   ```bash
   cd server
   source .venv/bin/activate
   python migrate_user_qr.py
   ```

2. **サーバー起動:**
   ```bash
   python run.py
   ```

3. **APIドキュメント確認:**
   ブラウザで `http://localhost:8000/docs` を開くとSwagger UIでAPIを確認できます。

---

## 変更履歴

### 2025-12-14
- ✅ Userテーブルに `qr_token`, `card_idm` カラムを追加
- ✅ `POST /login` エンドポイントを追加
- ✅ `GET /users/{user_id}/balance` エンドポイントを追加
- ✅ `POST /charge` エンドポイントを追加
- ✅ `POST /link_card` エンドポイントを追加
- ✅ `POST /register` レスポンスに `id` フィールドを追加
- ✅ 残高不足時の出場制限を実装
