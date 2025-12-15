# Felica Gate Server (FastAPI)

## クイックスタート（開発環境、SQLite）

### 1. 仮想環境の作成とインストール

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# 必要に応じて .env ファイルを編集
```

### 3. データベースの初期化とシードデータの投入

```bash
python seed_data.py
```

### 4. サーバーの起動

```bash
python run.py
```

サーバーは http://localhost:8000 で起動します。

## API ドキュメント

サーバー起動後、以下のURLでAPI仕様を確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要なエンドポイント

### スキャン処理
- `POST /scan` - FeliCa/QRコードのスキャン処理
  - 入場時は入場中のトリップを作成し、出場時は距離ベースの簡易運賃を計算して残高から減算します（レスポンスに `usage_amount` と更新後 `balance` を含みます）。

### 管理用エンドポイント

#### ユーザー管理
- `GET /users` - ユーザー一覧
- `GET /users/{user_id}` - ユーザー詳細
- `PATCH /users/{user_id}/balance` - 残高更新

#### 入退場履歴管理
- `GET /trips` - 入退場履歴一覧
- `GET /trips/{trip_id}` - 履歴詳細
- `PATCH /trips/{trip_id}/cancel` - 履歴をキャンセル

#### その他
- `GET /cards` - カード一覧
- `GET /cards/{card_id}` - カード詳細
- `GET /stations` - 駅一覧
- `GET /gates` - ゲート一覧

## データベース

デフォルトはSQLiteですが、本番環境ではPostgreSQLの使用を推奨します。
`.env` ファイルで `DATABASE_URL` を設定してください。

例（PostgreSQL）:
```
DATABASE_URL=postgresql://user:password@localhost:5432/felica_gate
```

## 注意事項

これはプロトタイプです。本番環境では以下を追加してください：
- 認証・認可機能
- より厳密なバリデーション
- PostgreSQLなどの本格的なデータベース
- セキュリティ対策（HTTPS、CORS設定の最適化など）
