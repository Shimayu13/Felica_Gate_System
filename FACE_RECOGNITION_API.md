# 顔認証API使用ガイド

## 概要

DeepFaceライブラリを使用した顔認証システムです。ユーザーの顔画像をBase64形式で送信し、顔の特徴量を抽出・比較します。

## 実装済み機能

### 1. 顔登録 API

**エンドポイント**: `POST /face/register`

**用途**: ユーザーの顔を登録し、特徴量をデータベースに保存

**リクエスト**:
```json
{
  "user_id": 3,
  "face_image_base64": "iVBORw0KGgoAAAANS..." // Base64エンコードされた顔画像（JPEG/PNG）
}
```

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "顔の登録に成功しました",
  "user_id": 3,
  "user_name": "鈴木一郎",
  "embedding_dim": 128
}
```

**レスポンス（エラー）**:
```json
{
  "status": "error",
  "message": "顔の登録に失敗: 顔が検出できませんでした"
}
```

### 2. 顔認証 API

**エンドポイント**: `POST /face/verify`

**用途**: 顔画像を送信し、登録済みユーザーと照合

**リクエスト**:
```json
{
  "face_image_base64": "iVBORw0KGgoAAAANS..." // Base64エンコードされた顔画像
}
```

**レスポンス（認証成功）**:
```json
{
  "status": "success",
  "verified": true,
  "user_id": 3,
  "user_name": "鈴木一郎",
  "balance": 18750.0,
  "distance": 0.3245,  // 特徴量の距離（小さいほど似ている）
  "similarity": 67.55,  // 類似度（%）
  "threshold": 0.6  // 認証閾値
}
```

**レスポンス（認証失敗）**:
```json
{
  "status": "error",
  "verified": false,
  "message": "顔認証に失敗しました"
}
```

### 3. 顔登録 API（ファイルアップロード版）⭐️ おすすめ

**エンドポイント**: `POST /face/register/upload`

**用途**: 画像ファイルを直接アップロードして顔を登録（テスト用）

**リクエスト**: Form-data形式
- `user_id`: ユーザーID（整数）
- `file`: 顔画像ファイル（JPEG/PNG）

**使い方**:
1. ブラウザで `http://localhost:8000/docs` を開く
2. `POST /face/register/upload` のセクションを開く
3. 「Try it out」をクリック
4. `user_id` に登録したいユーザーIDを入力（例: 3）
5. 「Choose File」をクリックして画像ファイルを選択
6. 「Execute」をクリック

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "顔の登録に成功しました",
  "user_id": 3,
  "user_name": "鈴木一郎",
  "embedding_dim": 128
}
```

### 4. 顔認証 API（ファイルアップロード版）⭐️ おすすめ

**エンドポイント**: `POST /face/verify/upload`

**用途**: 画像ファイルを直接アップロードして顔認証（テスト用）

**リクエスト**: Form-data形式
- `file`: 顔画像ファイル（JPEG/PNG）

**使い方**:
1. ブラウザで `http://localhost:8000/docs` を開く
2. `POST /face/verify/upload` のセクションを開く
3. 「Try it out」をクリック
4. 「Choose File」をクリックして画像ファイルを選択
5. 「Execute」をクリック

**レスポンス（認証成功）**:
```json
{
  "status": "success",
  "verified": true,
  "user_id": 3,
  "user_name": "鈴木一郎",
  "balance": 18750.0,
  "distance": 0.3245,
  "similarity": 67.55,
  "threshold": 0.6
}
```

**レスポンス（認証失敗）**:
```json
{
  "status": "error",
  "verified": false,
  "message": "顔認証に失敗しました"
}
```

## 技術詳細

### 使用ライブラリ

- **DeepFace 0.0.92**: 顔認証フレームワーク
- **Facenet**: 顔の特徴量抽出モデル（128次元ベクトル）
- **OpenCV**: 顔検出バックエンド
- **TensorFlow/Keras**: ディープラーニングフレームワーク

### 認証アルゴリズム

1. **特徴量抽出**:
   - Facenetモデルで顔画像から128次元の特徴量ベクトルを抽出

2. **類似度計算**:
   - L2距離（ユークリッド距離）で特徴量を比較
   - 距離が閾値（デフォルト: 0.6）以下なら認証成功

3. **ベストマッチ選択**:
   - 複数のユーザーが登録されている場合、最も距離が近いユーザーを選択

### 認証精度の調整

`main.py`の`verify_face`関数内で閾値を調整できます：

```python
threshold=0.6  # Facenetの推奨閾値（調整可能）
```

- **閾値を小さくする（例: 0.4）**: より厳しい認証（誤認識を減らす）
- **閾値を大きくする（例: 0.8）**: より緩い認証（認証失敗を減らす）

## テスト方法

### 方法1: Python requestsライブラリを使用

```python
import requests
import base64

# 画像ファイルをBase64エンコード
with open("face_image.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()

# 顔登録
response = requests.post(
    "http://localhost:8000/face/register",
    json={
        "user_id": 3,
        "face_image_base64": encoded_string
    }
)
print(response.json())

# 顔認証
response = requests.post(
    "http://localhost:8000/face/verify",
    json={
        "face_image_base64": encoded_string
    }
)
print(response.json())
```

### 方法2: curlコマンド

```bash
# 画像をBase64エンコード
BASE64_IMAGE=$(base64 -i face_image.jpg)

# 顔登録
curl -X POST http://localhost:8000/face/register \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": 3, \"face_image_base64\": \"$BASE64_IMAGE\"}"

# 顔認証
curl -X POST http://localhost:8000/face/verify \
  -H "Content-Type: application/json" \
  -d "{\"face_image_base64\": \"$BASE64_IMAGE\"}"
```

### 方法3: iOS アプリから使用

```swift
// カメラで顔を撮影
let image = capturedImage

// UIImageをBase64エンコード
guard let imageData = image.jpegData(compressionQuality: 0.8) else { return }
let base64String = imageData.base64EncodedString()

// 顔登録リクエスト
let registerRequest = [
    "user_id": 3,
    "face_image_base64": base64String
]

// APIに送信
// ... (APIClient実装が必要)
```

## データベース構造

### face_dataテーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | Integer | 主キー |
| user_id | Integer | ユーザーID（外部キー、ユニーク） |
| face_encoding | String | JSON形式の顔特徴量（128次元配列） |
| registered_at | DateTime | 登録日時 |
| updated_at | DateTime | 更新日時 |
| is_active | Integer | 有効フラグ（1=有効、0=無効） |

## 今後の拡張

### iOS アプリ実装（未実装）

1. **FaceCaptureView**: カメラで顔を撮影するビュー
2. **Face認証モード**: 改札で顔認証を使って入退場
3. **顔登録画面**: ユーザー登録時に顔を登録

### 改札連携（未実装）

- `/scan/face` エンドポイント: 顔認証での入退場処理
- 既存の `/scan` エンドポイントと同様の機能
- QRコードの代わりに顔認証を使用

## セキュリティとプライバシー

### 現在の実装

- ✅ 顔画像は一時保存後すぐに削除
- ✅ 顔の特徴量のみをデータベースに保存
- ✅ 元の顔画像は復元不可能

### 本番環境での推奨事項

- ⚠️ HTTPS通信の使用
- ⚠️ 顔データの暗号化
- ⚠️ GDPR/個人情報保護法への対応
- ⚠️ ユーザーの同意取得
- ⚠️ データ削除機能の実装

## トラブルシューティング

### エラー: "顔が検出できませんでした"

**原因**:
- 画像に顔が写っていない
- 顔が小さすぎる
- 画像が暗すぎる/明るすぎる
- 顔が横を向いている

**解決策**:
- 正面を向いた明るい顔写真を使用
- 顔が画像の中央に大きく写るように調整

### エラー: "顔認証に失敗しました"

**原因**:
- 登録された顔と異なる
- 閾値が厳しすぎる
- 照明条件が登録時と大きく異なる

**解決策**:
- 閾値を調整（0.6 → 0.8など）
- 同じ人の顔を再登録
- 複数の角度・照明で顔を登録

## パフォーマンス

### 処理時間（目安）

- **顔登録**: 約1-3秒（初回モデルロード時は5-10秒）
- **顔認証（1ユーザー）**: 約1-3秒
- **顔認証（10ユーザー）**: 約3-5秒

### 最適化

- 登録ユーザー数が多い場合は、インデックスやキャッシュの実装を推奨
- GPUを使用すると大幅に高速化可能

## まとめ

顔認証APIの基本実装が完了しました。サーバー側のAPIは動作可能で、テスト用の顔画像があればすぐに試せます。

iOS側の実装は別途必要ですが、API仕様は確定しているため、カメラキャプチャとBase64エンコード機能を追加すれば動作します。
