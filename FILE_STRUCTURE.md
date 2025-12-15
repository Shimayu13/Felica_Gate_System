# ファイル構造とディレクトリガイド

このドキュメントでは、プロジェクト内のファイルとディレクトリの役割を説明します。

## 📂 ディレクトリ構成

```
Felica_Gate_System/
│
├── 📱 Felica_Gate_System/          ← ✅ iOSアプリの実際のソースコード（Xcodeプロジェクト）
│   ├── ContentView.swift           メインUI
│   ├── NFCReader.swift             NFC読み取り機能
│   ├── QRScannerView.swift         QRコードスキャナー
│   ├── APIClient.swift             API通信クライアント
│   ├── Felica_Gate_SystemApp.swift アプリエントリーポイント
│   └── Assets.xcassets/            画像・アイコン
│
├── 🔧 Felica_Gate_System.xcodeproj/ ← Xcodeプロジェクトファイル
│   └── project.pbxproj             プロジェクト設定
│
├── 🖥️ server/                      ← バックエンドAPI
│   ├── main.py                     FastAPIアプリケーション
│   ├── models.py                   データベースモデル
│   ├── schemas.py                  APIスキーマ定義
│   ├── database.py                 DB接続設定
│   ├── seed_data.py                テストデータ投入
│   ├── run.py                      サーバー起動スクリプト
│   ├── requirements.txt            Python依存関係
│   ├── .env.example                環境変数サンプル
│   ├── migrations/
│   │   └── 001_init.sql            初期スキーマ
│   └── README.md
│
├── 🌐 webapp/admin-panel/          ← 管理画面（Next.js）
│   ├── app/
│   │   ├── page.tsx                ダッシュボード
│   │   ├── layout.tsx              レイアウト
│   │   ├── globals.css             グローバルスタイル
│   │   ├── users/page.tsx          ユーザー管理画面
│   │   ├── trips/page.tsx          入退場履歴画面
│   │   └── cards/page.tsx          カード管理画面
│   ├── package.json                npm依存関係
│   ├── tsconfig.json               TypeScript設定
│   ├── tailwind.config.ts          Tailwind設定
│   └── README.md
│
├── 📚 ios/                         ← 参考資料とドキュメント（直接使用しない）
│   ├── APIClient.swift             サンプルコード
│   ├── ContentView-Sample.swift    サンプルコード
│   ├── NFCReader.swift             サンプルコード
│   ├── QRScanner.swift             サンプルコード
│   ├── SETUP.md                    ✅ セットアップ手順（重要）
│   └── README.md
│
├── 📁 admin/                       ← 旧管理画面（シンプルなHTML版、参考用）
│
├── 📖 README.md                    ← プロジェクト全体の説明
├── 🚀 QUICKSTART.md                ← 5分でセットアップするガイド
├── 🏗️ ARCHITECTURE.md              ← システムアーキテクチャ詳細
├── 📋 FILE_STRUCTURE.md            ← このファイル
└── .gitignore                      Git除外設定
```

## 🎯 どのファイルを編集すべきか

### iOSアプリを開発する場合

**✅ 編集する**: `Felica_Gate_System/` ディレクトリ内のファイル
- `Felica_Gate_System/ContentView.swift`
- `Felica_Gate_System/NFCReader.swift`
- `Felica_Gate_System/QRScannerView.swift`
- `Felica_Gate_System/APIClient.swift`

**❌ 編集しない**: `ios/` ディレクトリ（参考資料のみ）

### サーバーを開発する場合

**✅ 編集する**: `server/` ディレクトリ内のファイル
- `server/main.py` - APIエンドポイントの追加・変更
- `server/models.py` - データベースモデルの追加・変更
- `server/schemas.py` - APIスキーマの追加・変更

### 管理画面を開発する場合

**✅ 編集する**: `webapp/admin-panel/` ディレクトリ内のファイル
- `webapp/admin-panel/app/page.tsx` - ダッシュボードの変更
- `webapp/admin-panel/app/users/page.tsx` - ユーザー管理画面の変更
- `webapp/admin-panel/app/trips/page.tsx` - 履歴管理画面の変更

## 🔍 よくある質問

### Q1: `ios/` と `Felica_Gate_System/` の違いは？

**A**:
- `Felica_Gate_System/` → **実際に使用されるXcodeプロジェクトのソースコード**
- `ios/` → **参考資料とドキュメント**（セットアップ手順が含まれる）

Xcodeで開発する際は `Felica_Gate_System/` のファイルを編集します。

### Q2: Xcodeで開くファイルは？

**A**: プロジェクトルートから以下のコマンドで開きます：

```bash
open Felica_Gate_System.xcodeproj
```

### Q3: なぜ `ios/` ディレクトリがあるの？

**A**: 以下の理由で残しています：
1. セットアップ手順（`SETUP.md`）が含まれている
2. 新しい開発者がコードの構造を理解するのに役立つ
3. バックアップとして機能する
4. プロジェクトの初期テンプレートとして参照できる

### Q4: どのSwiftファイルをXcodeに追加すればいい？

**A**: すでに以下のファイルが `Felica_Gate_System/` に配置されています：
- ✅ ContentView.swift
- ✅ NFCReader.swift
- ✅ QRScannerView.swift
- ✅ APIClient.swift
- ✅ Felica_Gate_SystemApp.swift

これらのファイルをXcodeプロジェクトに追加してください。

## 📝 開発ワークフロー

### iOSアプリの開発

1. `Felica_Gate_System.xcodeproj` をXcodeで開く
2. `Felica_Gate_System/` 内のSwiftファイルを編集
3. ビルドして実機でテスト

### サーバーの開発

1. `server/` ディレクトリに移動
2. Pythonファイルを編集
3. `python run.py` でサーバー起動してテスト

### 管理画面の開発

1. `webapp/admin-panel/` ディレクトリに移動
2. TypeScript/TSXファイルを編集
3. `npm run dev` で開発サーバー起動してテスト

## 🚨 重要な注意事項

### ❌ やってはいけないこと

1. `ios/` ディレクトリのファイルを直接Xcodeプロジェクトで使用する
2. `Felica_Gate_System/` と `ios/` の両方を同時に編集する
3. `.xcodeproj` ファイルを手動で編集する

### ✅ 推奨される方法

1. `Felica_Gate_System/` のファイルのみを編集
2. `ios/SETUP.md` を参照してセットアップ
3. Xcodeの標準機能を使用してファイル管理

## 📖 関連ドキュメント

- [README.md](README.md) - プロジェクト全体の説明
- [QUICKSTART.md](QUICKSTART.md) - 5分でセットアップ
- [ARCHITECTURE.md](ARCHITECTURE.md) - システムアーキテクチャ
- [ios/SETUP.md](ios/SETUP.md) - iOSアプリのセットアップ手順
- [server/README.md](server/README.md) - サーバーAPI仕様
- [webapp/admin-panel/README.md](webapp/admin-panel/README.md) - 管理画面の機能
