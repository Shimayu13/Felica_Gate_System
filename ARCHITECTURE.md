# システムアーキテクチャ

## 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     FeliCa Gate System                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   iPhone     │      │   管理画面    │      │   Mac/iPad   │
│   アプリ      │      │  (Next.js)   │      │  / Browser   │
│              │      │              │      │              │
│ - CoreNFC    │      │ - Dashboard  │      │ - ユーザー管理│
│ - QR Scanner │      │ - Users List │      │ - 履歴確認   │
│ - SwiftUI    │      │ - Trips List │      │ - 残高変更   │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ HTTP POST /scan     │ HTTP GET/PATCH      │
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   FastAPI Server │
                    │   (REST API)     │
                    │                  │
                    │  - /scan         │
                    │  - /users        │
                    │  - /trips        │
                    │  - /cards        │
                    │  - /stations     │
                    │  - /gates        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   SQLAlchemy ORM │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Database       │
                    │   (SQLite/       │
                    │    PostgreSQL)   │
                    │                  │
                    │  - users         │
                    │  - cards         │
                    │  - trips         │
                    │  - stations      │
                    │  - gates         │
                    └──────────────────┘
```

## コンポーネント詳細

### 1. iPhoneアプリ (SwiftUI)

**責務**: FeliCaカード/QRコードのスキャンと結果表示

**主要ファイル**:
- `ContentView.swift` - メインUI
- `NFCReader.swift` - NFC読み取りロジック
- `QRScannerView.swift` - QRコードスキャナー
- `APIClient.swift` - HTTP通信

**技術スタック**:
- SwiftUI (UI)
- CoreNFC (FeliCa読み取り)
- AVFoundation (QRコードスキャン)
- URLSession (HTTP通信)

**フロー**:
```
1. ユーザーがスキャンボタンをタップ
2. NFCセッション開始 or カメラ起動
3. IDm or QRトークン取得
4. /scan APIにPOST
5. レスポンスを解析して結果表示
```

### 2. サーバー (FastAPI)

**責務**: ビジネスロジックとデータ管理

**主要ファイル**:
- `main.py` - APIエンドポイント定義
- `models.py` - データベースモデル
- `schemas.py` - Pydanticスキーマ
- `database.py` - DB接続設定
- `seed_data.py` - 初期データ投入

**技術スタック**:
- FastAPI (Webフレームワーク)
- SQLAlchemy (ORM)
- Pydantic (バリデーション)
- Uvicorn (ASGIサーバー)

**主要API**:

#### POST /scan
入場/出場処理の中核

```python
1. リクエストから IDm or QR トークンを取得
2. cards テーブルでカード検索
3. trips テーブルで進行中の旅程を検索
4. 進行中の旅程がある場合:
   - 出場処理: station_out, exited_at を更新、status=completed
5. 進行中の旅程がない場合:
   - 入場処理: 新規 trip レコード作成、status=in_progress
6. レスポンスを返す
```

#### 管理用API
- GET /users - ユーザー一覧
- PATCH /users/{id}/balance - 残高更新
- GET /trips - 履歴一覧
- PATCH /trips/{id}/cancel - 履歴キャンセル

### 3. 管理画面 (Next.js)

**責務**: データの可視化と管理操作

**主要ファイル**:
- `app/page.tsx` - ダッシュボード
- `app/users/page.tsx` - ユーザー管理
- `app/trips/page.tsx` - 履歴管理
- `app/cards/page.tsx` - カード管理

**技術スタック**:
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS

**機能**:
- 📊 統計情報のリアルタイム表示
- 👤 ユーザー一覧と詳細表示
- 💰 残高の手動変更
- 📝 入退場履歴の一覧・フィルタリング
- ❌ 誤った記録のキャンセル

### 4. データベース

**スキーマ**:

```sql
users
├── id (PK)
├── name
├── email
└── balance

cards
├── id (PK)
├── user_id (FK → users)
├── idm (FeliCa用、UNIQUE)
├── qr_token (QR用、UNIQUE)
└── label

trips
├── id (PK)
├── user_id (FK → users)
├── card_id (FK → cards)
├── station_in
├── gate_in
├── station_out
├── gate_out
├── status (in_progress/completed/cancelled)
├── entered_at
├── exited_at
└── device_id

stations
├── id (PK)
├── code (UNIQUE)
└── name

gates
├── id (PK)
├── code (UNIQUE)
├── station_id (FK → stations)
└── name
```

## データフロー

### 入場処理

```
[iPhone] FeliCaスキャン
    ↓
[iPhone] IDm取得: "0123456789ABCDEF"
    ↓
[iPhone] POST /scan {
    scan_source: "felica",
    card_idm: "0123456789ABCDEF",
    station_code: "ST01",
    gate_code: "A1"
}
    ↓
[Server] cards テーブルで IDm検索
    ↓
[Server] card.user_id = 1 (田中太郎)
    ↓
[Server] trips テーブルで進行中の旅程を検索
    ↓
[Server] なし → 入場処理
    ↓
[Server] INSERT INTO trips (
    user_id=1,
    card_id=1,
    station_in="ST01",
    gate_in="A1",
    status="in_progress"
)
    ↓
[Server] { "mode": "entry" }
    ↓
[iPhone] "入場しました" を表示
```

### 出場処理

```
[iPhone] 同じFeliCaスキャン
    ↓
[Server] trips テーブルで進行中の旅程を検索
    ↓
[Server] あり → 出場処理
    ↓
[Server] UPDATE trips SET
    station_out="ST02",
    gate_out="B1",
    exited_at=NOW(),
    status="completed"
WHERE id=xxx
    ↓
[Server] { "mode": "exit" }
    ↓
[iPhone] "出場しました" を表示
```

## セキュリティ考慮事項

### 現在の実装（プロトタイプ）
- ❌ 認証なし
- ❌ 認可なし
- ✅ CORS有効（全オリジン許可）
- ⚠️ HTTPSなし

### 本番環境で必要な対策
- ✅ JWT認証
- ✅ ユーザーごとの権限管理
- ✅ CORS制限（許可されたオリジンのみ）
- ✅ HTTPS/TLS
- ✅ レート制限
- ✅ 入力バリデーション強化
- ✅ SQLインジェクション対策
- ✅ XSS対策

## スケーラビリティ

### 現在の構成
- 単一サーバー
- SQLite（開発用）
- 同期処理

### スケールアウト時の推奨構成
```
[Load Balancer]
    ↓
[API Server 1] [API Server 2] [API Server N]
    ↓           ↓               ↓
[PostgreSQL Primary]
    ↓
[PostgreSQL Replica 1] [PostgreSQL Replica 2]
```

### 推奨技術
- **Database**: PostgreSQL (Read Replica構成)
- **Cache**: Redis
- **Queue**: Celery / RabbitMQ
- **Container**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana

## 拡張ポイント

### 1. 料金計算機能
```python
# trips 完了時に料金計算
def calculate_fare(station_in, station_out):
    # 距離ベースまたは固定料金
    # user.balance から減算
```

### 2. リアルタイム通知
```
WebSocket を使用して管理画面に
リアルタイムで入退場情報を表示
```

### 3. 分析機能
```
- 時間帯別の利用状況
- 駅別の入場/出場数
- ユーザーごとの利用パターン
```

### 4. モバイルWeb版
```
レスポンシブ対応の強化により
スマートフォンからも管理可能に
```

## 開発ガイドライン

### コーディング規約
- Python: PEP 8
- TypeScript: Prettier + ESLint
- Swift: Swift API Design Guidelines

### コミット規約
```
feat: 新機能
fix: バグ修正
docs: ドキュメント
refactor: リファクタリング
test: テスト追加
```

### テスト戦略
- Backend: pytest
- Frontend: Jest + React Testing Library
- E2E: Playwright
