# アプリケーション構成

FeliCa Gate Systemは3つの独立したアプリケーションで構成されています。

## 📱 1. 改札機アプリ (Gate App)

**プロジェクト**: `Felica_Gate_System.xcodeproj`

### 機能
- ✅ QRコードスキャン
- ✅ FeliCaスキャン（将来実装）
- ✅ 入退場記録の作成
- ✅ 駅・ゲート設定
- ⏳ 物販モード（将来実装）

### ファイル構成
```
Felica_Gate_System/
├── ContentView.swift          # メインビュー（タブ切り替え）
├── GateView.swift             # QRスキャン画面（ContentView内）
├── GateSettingsView.swift     # 設定画面
├── QRScannerView.swift        # QRスキャナーコンポーネント
├── NFCReader.swift            # NFCリーダー（将来使用）
├── APIClient.swift            # API通信クライアント
└── Felica_Gate_SystemApp.swift # アプリエントリーポイント
```

### 設定項目
- サーバーURL
- 駅コード
- ゲートコード
- 動作モード（交通改札 / 物販レジ）

### 使用方法
1. Xcodeで `Felica_Gate_System.xcodeproj` を開く
2. 「設定」タブでサーバーURL、駅、ゲートを設定
3. 「スキャン」タブに戻る
4. QRコードをスキャンして入退場記録

---

## 👤 2. ユーザーアプリ (User App)

**ディレクトリ**: `User_App/` （新規Xcodeプロジェクトとして作成予定）

### 機能
- ✅ アカウント登録
- ✅ QRコード生成・表示
- ⏳ FeliCa IDm登録（将来実装）
- ⏳ 残高確認

### 必要なファイル（移行予定）
```
User_App/
├── UserRegistrationView.swift  # アカウント登録画面
├── QRCodeDisplayView.swift    # QRコード表示（UserRegistrationView内）
├── APIClient.swift            # API通信クライアント（共通）
└── UserApp.swift              # アプリエントリーポイント
```

### 作成手順
1. Xcodeで新規iOSプロジェクト作成
   - Product Name: `User_App`
   - Organization Identifier: `com.yourcompany.userapp`
   - Interface: SwiftUI
   - Life Cycle: SwiftUI App

2. 以下のファイルをコピー：
   - `Felica_Gate_System/UserRegistrationView.swift` → `User_App/`
   - `Felica_Gate_System/APIClient.swift` → `User_App/`

3. `ContentView.swift`を以下に置き換え：
```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        UserRegistrationView()
    }
}
```

---

## 🖥️ 3. 管理アプリ (Admin App)

**ディレクトリ**: `admin/`

### 機能
- ✅ ユーザー一覧・管理
- ✅ 入退場記録一覧
- ✅ 駅・ゲート管理
- ✅ カード一覧
- ✅ 残高調整
- ✅ トリップキャンセル

### ファイル構成
```
admin/
├── index.html    # メインHTML
├── styles.css    # スタイルシート
├── api.js        # API通信・UI制御
└── README.md     # ドキュメント
```

### 起動方法
```bash
cd admin
python3 -m http.server 3000
```

ブラウザで `http://localhost:3000` を開く

---

## 🔄 アプリケーション間の連携

```
┌─────────────────┐
│  ユーザーアプリ  │ ──┐
│  (User App)     │   │
└─────────────────┘   │
                      │  POST /register
                      │  QRトークン発行
                      ↓
              ┌──────────────┐
              │   サーバー    │
              │  (FastAPI)   │
              └──────────────┘
                      ↑
                      │  POST /scan
                      │  GET /users
                      │  GET /cards
┌─────────────────┐   │
│  改札機アプリ    │ ──┘
│  (Gate App)     │
└─────────────────┘

┌─────────────────┐
│  管理アプリ      │ ──→ GET/PATCH /users, /trips, /cards
│  (Admin App)    │     サーバー管理・監視
└─────────────────┘
```

## 🚀 システム全体の起動手順

### 1. サーバー起動
```bash
cd server
source .venv/bin/activate
python run.py
```

### 2. 管理アプリ起動（オプション）
```bash
cd admin
python3 -m http.server 3000
```

### 3. 改札機アプリ起動
- Xcodeで `Felica_Gate_System.xcodeproj` を開く
- iPhoneまたはiPadにインストール
- 設定タブで駅・ゲート情報を設定

### 4. ユーザーアプリ起動
- Xcodeで `User_App` プロジェクトを開く（作成後）
- iPhoneまたはiPadにインストール
- アカウント登録してQRコード取得

## 📝 今後の拡張計画

### 改札機アプリ
- [ ] FeliCaスキャン実装
- [ ] 物販モード実装
- [ ] オフライン動作（ローカルキャッシュ）
- [ ] 音声フィードバック

### ユーザーアプリ
- [ ] FeliCa IDm登録機能
- [ ] リアルタイム残高確認
- [ ] 利用履歴表示
- [ ] チャージ機能

### 管理アプリ
- [ ] リアルタイム監視ダッシュボード
- [ ] 統計・分析機能
- [ ] CSVエクスポート
- [ ] 駅・ゲートの追加・編集UI
