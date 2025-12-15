# QRコードテスト用ガイド

## テスト用QRコードの生成

シードデータで登録されているQRトークンのQRコードを生成して、アプリでテストできます。

### 登録されているQRトークン

シードデータ（`server/seed_data.py`）で以下のQRトークンが登録されています：

| ユーザー | QRトークン | 残高 |
|---------|-----------|------|
| 鈴木一郎 | `QR_SUZUKI_001` | ¥10,000 |

### QRコード生成方法

#### 方法1: オンラインQRコードジェネレーター（推奨・簡単）

1. [QR Code Generator](https://www.qr-code-generator.com/) にアクセス
2. **Text** を選択
3. 以下のテキストを入力：
   ```
   QR_SUZUKI_001
   ```
4. **Create QR Code** をクリック
5. 生成されたQRコードをスマートフォンで表示するか、印刷

#### 方法2: Pythonスクリプトで生成

```bash
cd server
pip install qrcode[pil]
python3 << EOF
import qrcode

# QRコードを生成
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data("QR_SUZUKI_001")
qr.make(fit=True)

# 画像として保存
img = qrcode.make("QR_SUZUKI_001")
img.save("qr_suzuki.png")
print("QRコードを qr_suzuki.png として保存しました")
EOF
```

#### 方法3: macOSのショートカットを使用

1. **ショートカット** アプリを開く
2. 新しいショートカットを作成
3. **テキスト** アクションを追加 → `QR_SUZUKI_001` と入力
4. **QRコードを生成** アクションを追加
5. **イメージを保存** または **共有** アクションを追加
6. ショートカットを実行

### テスト手順

#### 準備

1. サーバーが起動していることを確認
   ```bash
   cd server
   python run.py
   ```

2. MacのIPアドレスを確認
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   例: `inet 192.168.1.100`

3. iOSアプリの `ContentView.swift` (16行目) でサーバーURLを設定
   ```swift
   let apiClient = APIClient(baseURL: URL(string: "http://192.168.1.100:8000")!)
   ```

#### テスト実行

1. iOSアプリを起動
2. **QRコードをスキャン** ボタンをタップ
3. フロントカメラが起動
4. QRコードを画面に表示（PCの画面やスマートフォンなど）
5. カメラでQRコードを読み取る

#### 期待される結果

**初回スキャン（入場）:**
```
✓ 入場しました

👤 鈴木一郎

残高
¥10,000

🏢 ST01 / A1
```

**2回目スキャン（出場）:**
```
✓ 出場しました

👤 鈴木一郎

残高
¥10,000

🏢 ST01 / A1
```

### 追加のテストユーザーを作成

新しいQRカードを追加する場合：

1. サーバーのデータベースに直接追加（SQLite）
   ```bash
   cd server
   sqlite3 felica_gate.db
   ```

   ```sql
   -- 新しいユーザーを追加
   INSERT INTO users (name, email, balance) VALUES ('テスト太郎', 'test@example.com', 5000);

   -- ユーザーIDを確認（例: 4）
   SELECT id FROM users WHERE name = 'テスト太郎';

   -- QRカードを追加
   INSERT INTO cards (user_id, qr_token, label) VALUES (4, 'QR_TEST_001', 'テスト太郎のQRカード');

   -- 確認
   SELECT * FROM cards WHERE qr_token = 'QR_TEST_001';
   ```

2. `QR_TEST_001` のQRコードを生成

### トラブルシューティング

#### QRコードが読み取れない

- **フロントカメラの距離**: QRコードから20-30cm離す
- **明るさ**: 十分な照明があることを確認
- **QRコードのサイズ**: 小さすぎないか確認（最低5cm×5cm推奨）
- **画面の明るさ**: QRコードを表示している画面の明るさを最大に

#### カメラが起動しない

- Info.plistにカメラ権限が追加されているか確認
- iPhone設定で該当アプリのカメラ権限を確認

#### ネットワークエラー

- MacとiPhoneが同じWi-Fiに接続されているか確認
- サーバーが起動しているか確認: `http://localhost:8000/docs`
- ContentView.swiftのIPアドレスが正しいか確認

#### 「カード情報が見つかりません」エラー

- QRトークンがデータベースに登録されているか確認
  ```bash
  cd server
  sqlite3 felica_gate.db "SELECT * FROM cards WHERE qr_token = 'QR_SUZUKI_001';"
  ```

## デモ用QRコード一覧

テスト環境で使用できるQRコード：

### QR_SUZUKI_001（鈴木一郎）
- 残高: ¥10,000
- 用途: 基本的な入場/出場テスト

将来的に追加予定：
- QR_TANAKA_001（田中太郎）
- QR_SATO_001（佐藤花子）

### QRコード画像の保存場所

生成したQRコード画像は以下に保存することをお勧めします：
```
Felica_Gate_System/
└── qr_codes/
    ├── QR_SUZUKI_001.png
    ├── QR_TEST_001.png
    └── README.txt
```

## 本番環境での注意

- QRトークンは推測されにくいランダムな文字列を使用
- 有効期限の実装を検討
- QRコードの暗号化または署名を検討
- 使い捨てQRコード（ワンタイムトークン）の実装を検討
