# 定期券機能ドキュメント

## 概要

FeliCa Gate Systemに定期券機能が追加されました。定期券を持つユーザーは、指定区間内の乗車で運賃が0円になります。

## データベーススキーマ

### passesテーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| user_id | INTEGER | ユーザーID（外部キー） |
| pass_type | TEXT | 定期券種別（commuter: 通勤, student: 通学） |
| station_from | TEXT | 開始駅コード |
| station_to | TEXT | 終了駅コード |
| valid_from | TIMESTAMP | 有効期間開始日時 |
| valid_until | TIMESTAMP | 有効期間終了日時 |
| is_active | INTEGER | アクティブフラグ（1=有効、0=無効） |
| created_at | TIMESTAMP | 作成日時 |

### tripsテーブルの拡張

| カラム名 | 型 | 説明 |
|---------|-----|------|
| used_pass_id | INTEGER | 使用した定期券ID（外部キー、NULL可） |

## APIエンドポイント

### 1. 定期券作成
**エンドポイント:** `POST /passes`

**説明:** 新しい定期券を作成します。

**リクエストボディ:**
```json
{
  "user_id": 3,
  "pass_type": "commuter",
  "station_from": "ST01",
  "station_to": "ST02",
  "valid_from": "2025-12-01T00:00:00Z",
  "valid_until": "2026-02-28T23:59:59Z"
}
```

**パラメータ:**
- `user_id` (必須): ユーザーID
- `pass_type` (必須): 定期券種別（"commuter" または "student"）
- `station_from` (必須): 開始駅コード
- `station_to` (必須): 終了駅コード
- `valid_from` (必須): 有効期間開始日時（ISO 8601形式）
- `valid_until` (必須): 有効期間終了日時（ISO 8601形式）

**レスポンス:**
```json
{
  "status": "ok",
  "pass_id": 1,
  "message": "定期券を作成しました"
}
```

---

### 2. 定期券一覧取得
**エンドポイント:** `GET /passes`

**説明:** 定期券の一覧を取得します。

**クエリパラメータ:**
- `user_id` (オプション): 特定ユーザーの定期券のみ取得
- `skip` (オプション, デフォルト=0): スキップ件数
- `limit` (オプション, デフォルト=100): 取得件数

**例:**
```
GET /passes?user_id=3
```

**レスポンス:**
```json
[
  {
    "id": 1,
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "ST01",
    "station_to": "ST02",
    "valid_from": "2025-12-01T00:00:00",
    "valid_until": "2026-02-28T23:59:59",
    "is_active": 1,
    "created_at": "2025-12-14T01:36:03.346305"
  }
]
```

---

### 3. 定期券詳細取得
**エンドポイント:** `GET /passes/{pass_id}`

**説明:** 特定の定期券の詳細を取得します。

**パラメータ:**
- `pass_id` (パスパラメータ): 定期券ID

**レスポンス:**
```json
{
  "id": 1,
  "user_id": 3,
  "pass_type": "commuter",
  "station_from": "ST01",
  "station_to": "ST02",
  "valid_from": "2025-12-01T00:00:00",
  "valid_until": "2026-02-28T23:59:59",
  "is_active": 1,
  "created_at": "2025-12-14T01:36:03.346305"
}
```

---

### 4. ユーザーの定期券取得
**エンドポイント:** `GET /users/{user_id}/passes`

**説明:** 特定ユーザーの定期券を取得します。

**パラメータ:**
- `user_id` (パスパラメータ): ユーザーID
- `active_only` (クエリパラメータ, デフォルト=true): 有効な定期券のみ取得

**例:**
```
GET /users/3/passes?active_only=true
```

**レスポンス:**
```json
[
  {
    "id": 1,
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "ST01",
    "station_to": "ST02",
    "valid_from": "2025-12-01T00:00:00",
    "valid_until": "2026-02-28T23:59:59",
    "is_active": 1,
    "created_at": "2025-12-14T01:36:03.346305"
  }
]
```

---

### 5. 定期券無効化
**エンドポイント:** `PATCH /passes/{pass_id}/deactivate`

**説明:** 定期券を無効化します。

**パラメータ:**
- `pass_id` (パスパラメータ): 定期券ID

**レスポンス:**
```json
{
  "status": "ok",
  "message": "定期券を無効化しました"
}
```

---

## スキャンエンドポイントの拡張

### POST /scan の変更点

定期券を持つユーザーが出場する際、自動的に定期券が適用されます。

**出場時のレスポンス（定期券使用）:**
```json
{
  "mode": "exit",
  "user_id": 3,
  "balance": 20000.0,
  "usage_amount": 0.0,
  "used_pass": true,
  "pass_type": "commuter"
}
```

**出場時のレスポンス（通常運賃）:**
```json
{
  "mode": "exit",
  "user_id": 3,
  "balance": 19800.0,
  "usage_amount": 200.0,
  "used_pass": false
}
```

## 定期券の判定ロジック

1. **有効期間チェック**: `valid_from <= 現在時刻 <= valid_until`
2. **アクティブフラグチェック**: `is_active == 1`
3. **区間チェック**: 入場駅と出場駅が定期券の区間と一致（両方向対応）
   - `(station_from == 入場駅 AND station_to == 出場駅)` または
   - `(station_from == 出場駅 AND station_to == 入場駅)`

すべての条件を満たす定期券が見つかった場合、運賃0円で出場できます。

## 使用例

### 1. 定期券を作成

```bash
curl -X POST "http://localhost:8000/passes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "ST01",
    "station_to": "ST02",
    "valid_from": "2025-12-01T00:00:00Z",
    "valid_until": "2026-02-28T23:59:59Z"
  }'
```

### 2. 定期券で乗車

**入場（ST01）:**
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_source": "qr",
    "qr_token": "QR_SUZUKI_001",
    "station_code": "ST01",
    "gate_code": "A1",
    "timestamp": "2025-12-14T10:00:00Z",
    "device_id": "gate-001"
  }'
```

**出場（ST02）- 定期券が自動適用:**
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_source": "qr",
    "qr_token": "QR_SUZUKI_001",
    "station_code": "ST02",
    "gate_code": "B1",
    "timestamp": "2025-12-14T10:30:00Z",
    "device_id": "gate-002"
  }'
```

**レスポンス:**
```json
{
  "mode": "exit",
  "user_id": 3,
  "balance": 20000.0,
  "usage_amount": 0.0,
  "used_pass": true,
  "pass_type": "commuter"
}
```

### 3. 定期券区間外の乗車

**入場（ST01）:**
```bash
# 入場は定期券区間内でも区間外でも同じ
```

**出場（ST03）- 定期券適用外、通常運賃:**
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_source": "qr",
    "qr_token": "QR_SUZUKI_001",
    "station_code": "ST03",
    "gate_code": "C1",
    "timestamp": "2025-12-14T11:00:00Z",
    "device_id": "gate-003"
  }'
```

**レスポンス:**
```json
{
  "mode": "exit",
  "user_id": 3,
  "balance": 19750.0,
  "usage_amount": 250.0,
  "used_pass": false
}
```

## トリップ履歴での確認

定期券を使用した乗車は、`trips`テーブルの`used_pass_id`カラムに定期券IDが記録されます。

```bash
curl -X GET "http://localhost:8000/trips"
```

**レスポンス例:**
```json
[
  {
    "id": 10,
    "user_id": 3,
    "card_id": 3,
    "station_in": "ST01",
    "station_out": "ST02",
    "status": "completed",
    "used_pass_id": 1,
    ...
  }
]
```

## 注意事項

1. **定期券の重複**: 同じユーザーが同じ区間の定期券を複数持つことは可能ですが、最初に見つかった有効な定期券が使用されます。

2. **有効期限**: 定期券の有効期限は厳密にチェックされます。有効期限切れの定期券では通常運賃が適用されます。

3. **無効化**: 無効化された定期券（`is_active=0`）は使用できません。

4. **区間の方向**: 定期券は両方向で有効です。ST01→ST02とST02→ST01の両方で使用できます。

5. **残高チェック**: 定期券がある場合、残高チェックはスキップされます（運賃0円のため）。

## 管理アプリでの表示

管理アプリ（admin/index.html）に定期券セクションを追加することで、定期券の一覧や詳細を確認できます。

## ユーザーアプリでの表示

ユーザーアプリで自分の定期券を確認するには、`GET /users/{user_id}/passes`エンドポイントを使用します。

---

## マイグレーション

定期券機能を既存のデータベースに追加するには：

```bash
cd server
source .venv/bin/activate
python migrate_passes.py
```

## テストデータ

```sql
-- 鈴木一郎さん（user_id=3）に通勤定期券を作成
INSERT INTO passes (user_id, pass_type, station_from, station_to, valid_from, valid_until, is_active)
VALUES (3, 'commuter', 'ST01', 'ST02', '2025-12-01 00:00:00', '2026-02-28 23:59:59', 1);
```
