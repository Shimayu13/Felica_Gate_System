# トリップ管理画面の残高推移機能追加

## 更新日時
2025年12月14日

## 概要
管理画面のトリップ表示に残高推移、支払方法、運賃情報を追加し、ページネーション機能を実装しました。

---

## 実装した機能

### 1. 残高推移の記録と表示

#### データベース拡張
`trips`テーブルに以下のカラムを追加：
- `fare_amount` - 運賃額（REAL型）
- `balance_before` - 出場前の残高（REAL型）
- `balance_after` - 出場後の残高（REAL型）

#### 表示内容
- **出場前残高**: ユーザーが出場する直前の残高
- **出場後残高**: 運賃支払い後の残高
- **残高の増減**: 視覚的に表示（↓赤色で減少、→変化なし）

### 2. 支払方法の表示

各トリップの支払方法を色分けバッジで表示：
- **定期券** - 緑色バッジ（`used_pass_id`が存在する場合）
- **残高** - 青色バッジ（残高から運賃を支払った場合）
- **-** - グレー（入場中・キャンセル済み）

### 3. 運賃情報の表示

- 定期券使用時: **¥0**
- 残高支払い時: **¥200** など、実際の運賃額を表示
- 入場中: **-** （未確定）

### 4. ページネーション機能

#### 表示件数選択
- 20件
- 50件
- 100件（デフォルト）
- 全て

#### ページネーション機能
- 前へ/次へボタン
- ページ番号ボタン（最大5個表示）
- 現在のページをハイライト表示
- 表示中の範囲を表示（例: 1-100 / 150件）

#### ソート
- 新しい順に自動ソート（入場日時の降順）

---

## 変更したファイル

### バックエンド

#### 1. server/models.py
```python
class Trip(Base):
    # ... 既存のフィールド
    fare_amount = Column(Numeric(10,2), nullable=True)  # 運賃額
    balance_before = Column(Numeric(10,2), nullable=True)  # 出場前の残高
    balance_after = Column(Numeric(10,2), nullable=True)  # 出場後の残高
```

#### 2. server/main.py
出場処理時に残高情報を記録：

**定期券使用時:**
```python
current_balance = Decimal(card.user.balance or 0)
in_trip.fare_amount = Decimal(0)
in_trip.balance_before = current_balance
in_trip.balance_after = current_balance
```

**残高支払い時:**
```python
in_trip.fare_amount = fare
in_trip.balance_before = current_balance
in_trip.balance_after = current_balance - fare
```

#### 3. server/migrate_trip_balance.py
新規作成 - マイグレーションスクリプト
```bash
python migrate_trip_balance.py
```

### フロントエンド

#### 4. admin/index.html
トリップテーブルの拡張：
- 「支払方法」カラム追加
- 「運賃」カラム追加
- 「残高推移」カラム追加
- 「表示件数」フィルター追加
- ページネーション領域追加

#### 5. admin/styles.css
ページネーションスタイル追加：
- `.pagination` - ページネーション全体
- `.pagination button` - ページボタン
- `.pagination button.active` - アクティブなページ
- `.pagination-info` - 情報表示

#### 6. admin/api.js
主要な変更：
- `renderTrips()` - 残高情報、支払方法、運賃の表示ロジック追加
- `renderTripPagination()` - ページネーション表示ロジック
- `changeTripPage()` - ページ切り替え処理
- フィルター変更時のページリセット

---

## 表示例

### トリップテーブル表示

```
┌────┬────────┬─────────────┬─────────────┬──────────┬────────┬─────────────────┬────────┬────────┐
│ ID │ユーザー│   入場      │   出場      │ 支払方法 │  運賃  │   残高推移      │ステータス│ 操作   │
├────┼────────┼─────────────┼─────────────┼──────────┼────────┼─────────────────┼────────┼────────┤
│137 │   3    │ST01 (A1)    │ST02 (B1)    │ [定期券] │  ¥0    │  ¥19,500        │ 完了   │キャンセル│
│    │        │2025/12/14   │2025/12/14   │          │        │  → ¥19,500      │        │        │
├────┼────────┼─────────────┼─────────────┼──────────┼────────┼─────────────────┼────────┼────────┤
│136 │   3    │ST01 (A1)    │ST03 (C1)    │ [残高]   │ ¥250   │  ¥19,750        │ 完了   │キャンセル│
│    │        │2025/12/14   │2025/12/14   │          │        │  ↓ ¥19,500      │        │        │
├────┼────────┼─────────────┼─────────────┼──────────┼────────┼─────────────────┼────────┼────────┤
│135 │   3    │ST01 (A1)    │ST03 (C1)    │ [残高]   │ ¥250   │  ¥20,000        │ 完了   │キャンセル│
│    │        │2025/12/14   │2025/12/14   │          │        │  ↓ ¥19,750      │        │        │
└────┴────────┴─────────────┴─────────────┴──────────┴────────┴─────────────────┴────────┴────────┘
```

### ページネーション表示

```
« 前へ  [1]  2  3  4  5  ...  10  次へ »     1-100 / 150件
```

---

## 動作確認

### 1. 残高払いのトリップ
```bash
# 入場
curl -X POST 'http://localhost:8000/scan' \
  -H 'Content-Type: application/json' \
  -d '{"scan_source":"qr","qr_token":"QR_SUZUKI_001","station_code":"ST01","gate_code":"A1","timestamp":"2025-12-14T12:00:00Z","device_id":"gate-001"}'

# 出場（定期券区間外）
curl -X POST 'http://localhost:8000/scan' \
  -H 'Content-Type: application/json' \
  -d '{"scan_source":"qr","qr_token":"QR_SUZUKI_001","station_code":"ST03","gate_code":"C1","timestamp":"2025-12-14T12:30:00Z","device_id":"gate-003"}'
```

**結果:**
- `fare_amount`: 250.0
- `balance_before`: 20000.0
- `balance_after`: 19750.0
- `used_pass_id`: NULL

### 2. 定期券払いのトリップ
```bash
# 入場
curl -X POST 'http://localhost:8000/scan' \
  -H 'Content-Type: application/json' \
  -d '{"scan_source":"qr","qr_token":"QR_SUZUKI_001","station_code":"ST01","gate_code":"A1","timestamp":"2025-12-14T14:00:00Z","device_id":"gate-001"}'

# 出場（定期券区間内）
curl -X POST 'http://localhost:8000/scan' \
  -H 'Content-Type: application/json' \
  -d '{"scan_source":"qr","qr_token":"QR_SUZUKI_001","station_code":"ST02","gate_code":"B1","timestamp":"2025-12-14T14:30:00Z","device_id":"gate-002"}'
```

**結果:**
- `fare_amount`: 0.0
- `balance_before`: 19500.0
- `balance_after`: 19500.0
- `used_pass_id`: 1

---

## 既存データについて

### 注意事項
- 今回のアップデート以前に作成されたトリップには残高情報が記録されていません
- 既存トリップの`fare_amount`, `balance_before`, `balance_after`はNULL
- 管理画面では既存トリップの残高推移欄に「-」が表示されます

### 既存データの影響
- 既存トリップの表示には影響しません
- 新規トリップから自動的に残高情報が記録されます
- APIレスポンスに新しいフィールドが含まれます（後方互換性あり）

---

## 使い方

### 管理画面での確認

1. サーバー起動:
```bash
cd server
source .venv/bin/activate
python main.py
```

2. 管理画面を開く:
```
file:///Users/yuki/Developer/Felica_Gate_System/admin/index.html
```

3. 「📝 入退場記録（Trips）」セクションを確認

### フィルター機能

- **ステータスフィルター**: 全て / 入場中 / 完了 / キャンセル
- **表示件数**: 20件 / 50件 / 100件 / 全て

### ページネーション

- 表示件数を超える場合、自動的にページネーションが表示されます
- ページ番号をクリックして移動
- 「前へ」「次へ」ボタンで移動
- フィルター変更時は自動的に1ページ目に戻ります

---

## API レスポンス変更

### GET /trips

**新しいフィールド:**
```json
{
  "id": 137,
  "user_id": 3,
  "station_in": "ST01",
  "station_out": "ST02",
  "status": "completed",
  "used_pass_id": 1,
  "fare_amount": 0.0,
  "balance_before": 19500.0,
  "balance_after": 19500.0,
  ...
}
```

**既存トリップ（NULL値）:**
```json
{
  "id": 100,
  "user_id": 4,
  "station_in": "ST02",
  "station_out": "ST02",
  "status": "completed",
  "used_pass_id": null,
  "fare_amount": null,
  "balance_before": null,
  "balance_after": null,
  ...
}
```

---

## トラブルシューティング

### マイグレーションエラー

**エラー:** `duplicate column name`

**対処:** カラムは既に追加されています。問題ありません。

### 残高情報が表示されない

**原因:** 古いトリップデータ

**対処:** 新しいトリップを作成してテストしてください。

### ページネーションが表示されない

**原因:** トリップ数が表示件数以下

**対処:** 表示件数を減らすか、トリップを追加してください。

---

## まとめ

✅ **残高推移の完全な記録と表示**
- 出場前後の残高を記録
- 視覚的に増減を表示（色分け、矢印）

✅ **支払方法の明確な表示**
- 定期券使用を緑色バッジで表示
- 残高支払いを青色バッジで表示

✅ **運賃情報の表示**
- 定期券: ¥0
- 残高支払い: 実際の運賃額

✅ **ページネーション機能**
- 大量のトリップでも快適に閲覧
- 表示件数の選択可能
- ページ番号で簡単に移動

✅ **自動ソート**
- 新しいトリップが上に表示
- 最新の履歴を確認しやすい

これにより、管理画面からユーザーの残高推移と支払方法を完全に把握できるようになりました。

---

**実装者**: Claude Sonnet 4.5
**完了日**: 2025年12月14日
