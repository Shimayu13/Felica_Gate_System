# クイックスタートガイド

FeliCa Gate Systemを最速でセットアップして動かすためのガイドです。

## 必要な環境

- **サーバー**: Python 3.8以上
- **管理画面**: Node.js 18以上、npm
- **iOSアプリ**: macOS、Xcode 14以上、iPhone（実機）

## 5分でセットアップ

### ステップ1: サーバーを起動する

```bash
# リポジトリのルートディレクトリで
cd server

# 仮想環境を作成して有効化
python3 -m venv .venv
source .venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# テストデータを投入
python seed_data.py

# サーバーを起動
python run.py
```

✅ ブラウザで http://localhost:8000/docs を開いて、API仕様が表示されればOK！

### ステップ2: 管理画面を起動する

新しいターミナルウィンドウで：

```bash
# リポジトリのルートディレクトリで
cd webapp/admin-panel

# 依存関係をインストール（初回のみ）
npm install

# 開発サーバーを起動
npm run dev
```

✅ ブラウザで http://localhost:3000 を開いて、ダッシュボードが表示されればOK！

### ステップ3: iOSアプリをビルドする

1. Xcodeでプロジェクトを開く

```bash
# リポジトリのルートディレクトリで
open Felica_Gate_System.xcodeproj
```

2. Xcodeで `Felica_Gate_System` ターゲットを選択

3. 必要な設定を行う（詳細は [ios/SETUP.md](ios/SETUP.md) を参照）
   - Info.plistにNFCとカメラの権限を追加
   - CapabilitiesにNFC Tag Readingを追加
   - `Felica_Gate_System/ContentView.swift` のサーバーURLを実機のIPに変更

4. iPhoneを接続してビルド・実行

**注意**: 実際のソースコードは `Felica_Gate_System/` ディレクトリにあります。`ios/` ディレクトリは参考資料です。

✅ アプリが起動して、スキャンボタンが表示されればOK！

## 動作確認

### 1. 管理画面でデータを確認

http://localhost:3000 にアクセス

- ダッシュボード: 統計情報を確認
- ユーザー管理: 3人のテストユーザーを確認
- カード管理: 登録されたカードを確認

### 2. iOSアプリでFeliCaをスキャン

シードデータのIDmをシミュレート：
- `0123456789ABCDEF` (田中太郎さんのカード)
- `FEDCBA9876543210` (佐藤花子さんのカード)

または実際のFeliCaカード（Suica、PASMO等）をスキャン

### 3. 管理画面で履歴を確認

入退場履歴ページで、スキャン結果が表示されることを確認

## トラブルシューティング

### サーバーが起動しない

```bash
# Pythonのバージョンを確認
python3 --version  # 3.8以上が必要

# 依存関係を再インストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 管理画面が表示されない

```bash
# Node.jsのバージョンを確認
node --version  # 18以上が必要

# キャッシュをクリア
rm -rf node_modules .next
npm install
npm run dev
```

### iOSアプリがビルドできない

1. Xcodeのバージョンを確認（14以上）
2. [ios/SETUP.md](ios/SETUP.md) の設定手順を再確認
3. プロジェクトをクリーンビルド: Product > Clean Build Folder

### iPhoneからサーバーに接続できない

1. MacとiPhoneが同じWi-Fiネットワークに接続されているか確認
2. MacのIPアドレスを確認: `ifconfig | grep "inet "`
3. ContentView.swiftのURLを変更:

```swift
let apiClient = APIClient(baseURL: URL(string: "http://192.168.1.XXX:8000")!)
```

4. Macのファイアウォール設定でポート8000を許可

## 次のステップ

✅ 基本的な動作確認ができたら：

1. [README.md](README.md) でシステム全体の仕様を確認
2. [server/README.md](server/README.md) でAPIの詳細を確認
3. [webapp/admin-panel/README.md](webapp/admin-panel/README.md) で管理画面の機能を確認
4. 本番環境への展開を検討する場合は、README.mdの「本番環境への展開時の注意事項」を確認

## サポート

問題が解決しない場合は、以下を確認してください：

- サーバーのログ（ターミナルに表示）
- ブラウザのコンソール（F12で開く）
- Xcodeのコンソール

それでも解決しない場合は、エラーメッセージをコピーしてGitHub Issuesに報告してください。
