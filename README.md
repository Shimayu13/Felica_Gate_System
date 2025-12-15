# FeliCa Gate System

FeliCaカードまたはQRコードを使用した、ミニ改札システムのプロトタイプです。iPhoneで読み取った情報をサーバーに送信し、入場・出場の状態をセンターサーバー方式で管理します。

## システム構成

```
Felica_Gate_System/
├── server/                     # バックエンドAPI（FastAPI + SQLAlchemy）
├── Felica_Gate_System/         # ✅ iOSアプリ（SwiftUI + CoreNFC）- 実際のXcodeプロジェクト
│   ├── ContentView.swift       # メインUI
│   ├── NFCReader.swift         # NFC読み取り
│   ├── QRScannerView.swift     # QRスキャナー
│   ├── APIClient.swift         # API通信
│   └── Felica_Gate_SystemApp.swift
├── Felica_Gate_System.xcodeproj/  # Xcodeプロジェクトファイル
├── webapp/admin-panel/         # 管理画面（Next.js + TypeScript + Tailwind CSS）
├── ios/                        # 📚 iOSアプリの参考コードとドキュメント（参考用）
└── admin/                      # 旧管理画面（シンプルなHTML版、参考用）
```

### ⚠️ 重要：iOSアプリのソースコード

**実際のiOSアプリのコードは `Felica_Gate_System/` ディレクトリにあります。**

- ✅ 使用: `Felica_Gate_System/*.swift` - Xcodeプロジェクトの実際のソースコード
- 📚 参考: `ios/*.swift` - 参考用のサンプルコードとドキュメント

## 主な機能

### iPhoneアプリ
- ✅ FeliCa カードのIDm読み取り（CoreNFC使用）
- ✅ QRコードのスキャン（カメラ使用）
- ✅ サーバーへのスキャン情報送信（/scan API）
- ✅ 入場/出場結果の表示

### サーバー（REST API）
- ✅ データベース管理（users, cards, trips, stations, gates）
- ✅ /scan API: IDmまたはQRトークンでカード判定し、入場/出場処理
- ✅ 管理用API: ユーザー、カード、履歴の取得・更新

### 管理画面（Webアプリ）
- ✅ ダッシュボード（統計情報の表示）
- ✅ ユーザー管理（一覧、残高の確認・手動変更）
- ✅ 入退場履歴管理（一覧、絞り込み、キャンセル）
- ✅ カード管理（一覧表示）

## セットアップ手順

### 1. サーバーのセットアップ

```bash
cd server

# 仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# 必要に応じて .env を編集

# シードデータの投入
python seed_data.py

# サーバーの起動
python run.py
```

サーバーは http://localhost:8000 で起動します。

API仕様は以下で確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. 管理画面のセットアップ

```bash
cd webapp/admin-panel

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

管理画面は http://localhost:3000 で起動します。

### 3. iOSアプリのセットアップ

1. Xcodeでプロジェクトを開く

```bash
open Felica_Gate_System.xcodeproj
```

2. 必要なファイルをプロジェクトに追加
   - `Felica_Gate_System/NFCReader.swift`
   - `Felica_Gate_System/QRScannerView.swift`
   - `Felica_Gate_System/APIClient.swift`

3. `Info.plist` と Capabilities を設定（詳細は [ios/SETUP.md](ios/SETUP.md) を参照）

4. `ContentView.swift` のサーバーURL を環境に合わせて変更

```swift
// 実機の場合はMacのローカルIPを使用
let apiClient = APIClient(baseURL: URL(string: "http://192.168.1.XXX:8000")!)
```

5. 実機でビルド・実行（NFCとカメラ機能のため、シミュレータでは動作しません）

## API仕様

### POST /scan

FeliCaまたはQRコードのスキャン処理

**リクエスト:**
```json
{
  "scan_source": "felica",
  "card_idm": "0123456789ABCDEF",
  "qr_token": null,
  "station_code": "ST01",
  "gate_code": "A1",
  "timestamp": "2025-12-11T00:00:00Z",
  "device_id": "scanner-001"
}
```

**レスポンス:**
- 入場時: `{ "mode": "entry", "user_id": 1, "balance": 5000 }`
- 出場時: `{ "mode": "exit", "user_id": 1, "balance": 4800, "usage_amount": 200 }`
- エラー: `{ "status": "error", "message": "card_not_registered" }`

※ 出場時に自動で運賃が計算され、ユーザー残高から減算されます。`usage_amount` が引き落とし額、`balance` が処理後残高です。

### その他のAPI

- `GET /users` - ユーザー一覧
- `GET /users/{user_id}` - ユーザー詳細
- `PATCH /users/{user_id}/balance` - 残高更新
- `GET /trips` - 入退場履歴一覧
- `GET /trips/{trip_id}` - 履歴詳細
- `PATCH /trips/{trip_id}/cancel` - 履歴キャンセル
- `GET /cards` - カード一覧
- `GET /stations` - 駅一覧
- `GET /gates` - ゲート一覧

詳細は http://localhost:8000/docs を参照してください。

## データベース構造

### users
- id, name, email, balance

### cards
- id, user_id, idm (FeliCa), qr_token (QR), label

### trips
- id, user_id, card_id, station_in, gate_in, station_out, gate_out, status, entered_at, exited_at, device_id

### stations
- id, code, name

### gates
- id, code, station_id, name

## テストデータ

シードデータで以下が登録されます：

**ユーザー:**
- 田中太郎 (残高: ¥5,000)
- 佐藤花子 (残高: ¥3,000)
- 鈴木一郎 (残高: ¥10,000)

**カード:**
- 田中さんのFeliCa: IDm `0123456789ABCDEF`
- 佐藤さんのFeliCa: IDm `FEDCBA9876543210`
- 鈴木さんのQR: トークン `QR_SUZUKI_001`

**駅:**
- ST01: 東京駅
- ST02: 新宿駅
- ST03: 渋谷駅

## 開発環境

- **サーバー**: Python 3.8+, FastAPI, SQLAlchemy
- **iOSアプリ**: Swift 5.5+, SwiftUI, iOS 13+
- **管理画面**: Node.js 18+, Next.js 14, React 18, TypeScript 5

## 本番環境への展開時の注意事項

このシステムはプロトタイプです。本番環境で使用する場合は以下を実装してください：

### セキュリティ
- [ ] 認証・認可機能の追加（JWT, OAuth2など）
- [ ] HTTPS/TLSの使用
- [ ] CORS設定の適切な制限
- [ ] 入力バリデーションの強化
- [ ] レート制限の実装
- [ ] SQLインジェクション対策の確認

### データベース
- [ ] SQLiteからPostgreSQLへの移行
- [ ] データベースのバックアップ体制
- [ ] インデックスの最適化
- [ ] トランザクション処理の強化

### アプリケーション
- [ ] エラーハンドリングの改善
- [ ] ロギングの実装
- [ ] モニタリング・アラート機能
- [ ] 負荷分散・スケーリング対策

### 機能
- [ ] 料金計算機能
- [ ] 決済機能
- [ ] 通知機能
- [ ] レポート機能

## ライセンス

このプロジェクトはプロトタイプです。

## ドキュメント

### 🚀 はじめに
- [QUICKSTART.md](QUICKSTART.md) - 5分でセットアップする方法
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md) - ファイル構造とディレクトリガイド

### 📚 詳細ドキュメント
- [ARCHITECTURE.md](ARCHITECTURE.md) - システムアーキテクチャの詳細
- [server/README.md](server/README.md) - サーバーAPI仕様
- [ios/SETUP.md](ios/SETUP.md) - iOSアプリのセットアップ手順
- [webapp/admin-panel/README.md](webapp/admin-panel/README.md) - 管理画面の機能

### ⚠️ 重要
**iOSアプリのソースコード**: `Felica_Gate_System/` ディレクトリが実際のXcodeプロジェクトです。`ios/` は参考資料です。詳細は [FILE_STRUCTURE.md](FILE_STRUCTURE.md) を参照してください。
