# iOSアプリのセットアップ手順

⚠️ **重要**: NFCとカメラ機能を使用するため、**実機**でのテストが必須です。シミュレータでは動作しません。

## 📋 必須の設定（この順番で行ってください）

### ステップ1: プロジェクトを開く

```bash
open Felica_Gate_System.xcodeproj
```

### ステップ2: ⭐ Info.plist に権限の説明を追加（最重要！）

**アプリがクラッシュするのを防ぐため、まずこれを設定します。**

#### 方法A: Xcodeの設定画面から追加（👍 推奨・簡単）

1. プロジェクトナビゲータで **Felica_Gate_System** プロジェクト（青いアイコン）をクリック
2. **TARGETS** > **Felica_Gate_System** を選択
3. **Info** タブをクリック
4. **Custom iOS Target Properties** セクションで `+` ボタンをクリック

以下の2つを追加：

| キー（Xcodeで選択） | 用途 | 値（説明文） |
|-----|-----|-----|
| `Privacy - Camera Usage Description` | **QRコード**スキャン用 | `QRコードをスキャンするためにカメラを使用します` |
| `Privacy - NFC Scan Usage Description` | **FeliCa NFC**スキャン用 | `FeliCaカードを読み取るためにNFCを使用します` |

![Info.plist設定のイメージ]
```
Key                                      Type    Value
▼ Custom iOS Target Properties          Dictionary
  Privacy - Camera Usage Description     String  QRコードをスキャンするためにカメラを使用します
  Privacy - NFC Scan Usage Description   String  FeliCaカードを読み取るためにNFCを使用します
```

#### 方法B: Info.plistファイルから追加

プロジェクトナビゲータで `Info.plist` を見つけて右クリック > **Open As** > **Source Code** を選択し、以下を追加：

```xml
<key>NSCameraUsageDescription</key>
<string>QRコードをスキャンするためにカメラを使用します</string>

<key>NFCReaderUsageDescription</key>
<string>FeliCaカードを読み取るためにNFCを使用します</string>
```

### ステップ3: NFC Capability を追加

1. **TARGETS** > **Felica_Gate_System** を選択
2. **Signing & Capabilities** タブをクリック
3. **+ Capability** ボタン（左上）をクリック
4. 検索ボックスで「NFC」と入力
5. **Near Field Communication Tag Reading** をダブルクリック

✅ 追加されると、Capabilitiesリストに表示されます。
✅ 自動的に `.entitlements` ファイルが作成されます。

### ステップ4: FeliCa システムコードを追加

再び **Info** タブに戻り、`+` ボタンで以下を追加：

**キー**: `com.apple.developer.nfc.readersession.felica.systemcodes`
**タイプ**: Array

Arrayを展開して（▶をクリック）、以下の2つの文字列を追加：
- **Item 0**: `12FC`（交通系ICカード・Suica・PASMO用）
- **Item 1**: `0003`（FeliCa共通領域）

**Info.plistのソースコードで追加する場合：**

```xml
<key>com.apple.developer.nfc.readersession.felica.systemcodes</key>
<array>
    <string>12FC</string>
    <string>0003</string>
</array>
```

### ステップ5: Signing（署名）の設定

1. **Signing & Capabilities** タブ
2. **Team** で自分のApple IDを選択
3. **Bundle Identifier** が一意であることを確認（例: `com.yourname.Felica-Gate-System`）

### ステップ6: サーバーURLの変更（実機の場合）

`Felica_Gate_System/ContentView.swift` を開き、17行目付近を編集：

```swift
// Macのローカルネットワーク上のIPアドレスに変更
let apiClient = APIClient(baseURL: URL(string: "http://192.168.1.XXX:8000")!)
```

**MacのIPアドレスを確認する方法：**

```bash
# ターミナルで実行
ifconfig | grep "inet " | grep -v 127.0.0.1
```

例: `inet 192.168.1.100` → URLは `http://192.168.1.100:8000`

## 🚀 ビルドと実行

### 1. クリーンビルド

```
Product > Clean Build Folder (⌘ + Shift + K)
```

### 2. iPhoneを接続

1. USBケーブルでiPhoneをMacに接続
2. iPhoneで「このコンピュータを信頼しますか？」が表示されたら **信頼** をタップ
3. Xcodeの上部中央で、接続したiPhoneを選択

### 3. ビルド・実行

```
Product > Run (⌘ + R)
```

### 4. 初回実行時の設定

初回はiPhoneに以下の警告が表示されます：

**「信頼されていない開発元」**

1. iPhoneの **設定** アプリを開く
2. **一般** > **VPNとデバイス管理** または **デバイス管理**
3. 自分のApple IDをタップ
4. **"[Apple ID]"を信頼** をタップ
5. アプリを再度起動

## ✅ 動作確認

### 1. アプリが起動する
- 「FeliCa Gate System」というタイトルが表示される
- 「FeliCaをスキャン」と「QRコードをスキャン」のボタンが表示される

### 2. QRコードスキャンのテスト
1. 「QRコードをスキャン」ボタンをタップ
2. カメラ権限を求められたら **許可** をタップ
3. カメラが起動すればOK

### 3. NFCスキャンのテスト
1. 「FeliCaをスキャン」ボタンをタップ
2. 「FeliCaカードをiPhoneに近づけてください」と表示される
3. Suica、PASMO、nanaco等のカードを近づける
4. 読み取り成功またはエラーメッセージが表示されればOK

## 🔧 トラブルシューティング

### ❌ アプリがクラッシュする（プライバシー関連のエラー）

```
This app has crashed because it attempted to access privacy-sensitive data...
```

**原因**: Info.plistに `NSCameraUsageDescription` または `NFCReaderUsageDescription` が不足

**解決**: ステップ2を再確認し、両方のキーが追加されているか確認

### ❌ NFC XPCエラー

```
Error Domain=NSCocoaErrorDomain Code=4099 "...nfcd.service.corenfc..."
```

**原因1**: NFC Capabilityが追加されていない
**解決**: ステップ3を実行

**原因2**: Entitlementsが正しく設定されていない
**解決**: `.entitlements` ファイルに以下が含まれているか確認

```xml
<key>com.apple.developer.nfc.readersession.formats</key>
<array>
    <string>NDEF</string>
    <string>TAG</string>
</array>
```

### ❌ FeliCaが読み取れない

**原因1**: システムコードが追加されていない
**解決**: ステップ4を実行

**原因2**: 対応していないデバイス
**確認**: iPhone 7以降、iOS 13以降が必要

### ❌ サーバーに接続できない

```
Network error: The Internet connection appears to be offline.
```

**原因**: MacとiPhoneが同じWi-Fiに接続されていない、またはサーバーが起動していない

**解決**:
1. Macでサーバーが起動しているか確認: `http://localhost:8000/docs`
2. MacとiPhoneが同じWi-Fiネットワークに接続されているか確認
3. Macのファイアウォールでポート8000が許可されているか確認
4. ContentView.swiftのURLが正しいか確認

## 📱 対応デバイス

| 機能 | 要件 |
|------|------|
| NFC (FeliCa) | iPhone 7以降、iOS 13以降 |
| QRコード | カメラ搭載のiPhone、iOS 13以降 |

## 🔒 本番環境での追加設定

プロトタイプを超えて本番環境で使用する場合：

- [ ] App Store ConnectでNFC Entitlementを申請
- [ ] HTTPSを使用（ATSの設定）
- [ ] 適切なBundle IDとProvisioning Profileの設定
- [ ] エラーハンドリングの強化
- [ ] ログ記録の実装

## 📚 参考リンク

- [Apple - Core NFC](https://developer.apple.com/documentation/corenfc)
- [Apple - NFCTagReaderSession](https://developer.apple.com/documentation/corenfc/nfctagreadersession)
- [Apple - Info.plist Keys](https://developer.apple.com/documentation/bundleresources/information_property_list)
