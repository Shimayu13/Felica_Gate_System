# ユーザーアプリ - FeliCa登録機能 実装ガイド

## 概要
ユーザーアプリにFeliCaカード（Suica/PASMO等）のIDm登録機能を追加し、QRコードとFeliCaカードの両方で改札を利用できるようにします。

## 前提条件
- サーバー側API: `/link_card` エンドポイントが実装済み
- ゲートシステム側: FeliCa読み取り機能が実装済み（NFCFeliCaReader）
- ユーザーはQRトークンでログイン済み

## 実装する機能

### 1. FeliCaカードスキャン画面

**UI要件:**
- ホーム画面に「FeliCaカードを登録」ボタンを追加
- タップするとNFCスキャン開始
- スキャン中のローディング表示
- 成功・失敗のフィードバック

**実装手順:**

#### Step 1: NFCFeliCaReaderの統合
既存のゲートシステムの `NFCFeliCaReader.swift` をユーザーアプリにコピー:

```swift
// FeliCa_Gate_System/NFCFeliCaReader.swift → UserApp/NFCFeliCaReader.swift
// そのまま使用可能
```

#### Step 2: FeliCa登録ビューの作成

```swift
import SwiftUI

struct RegisterFeliCaView: View {
    @Environment(\.dismiss) var dismiss
    @State private var isScanning = false
    @State private var resultMessage = ""
    @State private var showResult = false

    let qrToken: String
    let onSuccess: (String) -> Void

    private let feliCaReader = NFCFeliCaReader()

    var body: some View {
        VStack(spacing: 30) {
            Text("FeliCaカード登録")
                .font(.largeTitle)
                .fontWeight(.bold)

            Image(systemName: "wave.3.right.circle.fill")
                .font(.system(size: 100))
                .foregroundColor(.orange)

            Text("交通系ICカード（Suica・PASMO等）をiPhoneの背面にかざしてください")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            if isScanning {
                ProgressView()
                    .scaleEffect(1.5)
                Text("カードをかざしてください...")
                    .foregroundColor(.secondary)
            } else {
                Button(action: startScanning) {
                    HStack {
                        Image(systemName: "creditcard.fill")
                        Text("カードをスキャン")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.orange)
                    .cornerRadius(12)
                }
            }

            Spacer()
        }
        .padding()
        .alert("登録結果", isPresented: $showResult) {
            Button("OK") {
                if resultMessage.contains("成功") {
                    dismiss()
                }
            }
        } message: {
            Text(resultMessage)
        }
    }

    private func startScanning() {
        isScanning = true
        resultMessage = ""

        feliCaReader.startReading { result in
            DispatchQueue.main.async {
                isScanning = false

                switch result {
                case .success(let idm):
                    print("📇 FeliCa IDm: \(idm)")
                    linkCardToServer(idm: idm)

                case .failure(let error):
                    resultMessage = "スキャン失敗: \(error.localizedDescription)"
                    showResult = true
                }
            }
        }
    }

    private func linkCardToServer(idm: String) {
        // サーバーに送信
        let url = URL(string: "http://YOUR_SERVER_URL:8000/link_card")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = [
            "qr_token": qrToken,
            "card_idm": idm
        ]

        request.httpBody = try? JSONEncoder().encode(body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    resultMessage = "通信エラー: \(error.localizedDescription)"
                    showResult = true
                    return
                }

                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let status = json["status"] as? String {

                    if status == "ok" {
                        resultMessage = "FeliCaカードを登録しました！\nIDm: \(idm)"
                        showResult = true
                        onSuccess(idm)
                    } else {
                        resultMessage = "登録失敗: \(json["message"] as? String ?? "不明なエラー")"
                        showResult = true
                    }
                } else {
                    resultMessage = "サーバーエラー"
                    showResult = true
                }
            }
        }.resume()
    }
}
```

#### Step 3: ホーム画面への統合

```swift
struct HomeView: View {
    @State private var user: User?
    @State private var showRegisterFeliCa = false

    var body: some View {
        VStack(spacing: 20) {
            // ユーザー情報表示
            if let user = user {
                Text("こんにちは、\(user.name)さん")
                    .font(.title)

                Text("残高: ¥\(String(format: "%.0f", user.balance))")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                // QRコード表示
                QRCodeView(token: user.qrToken)

                // FeliCa登録ボタン
                if user.cardIdm == nil {
                    Button(action: { showRegisterFeliCa = true }) {
                        HStack {
                            Image(systemName: "creditcard.and.123")
                            Text("FeliCaカードを登録")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.orange)
                        .cornerRadius(12)
                    }
                } else {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("FeliCaカード登録済み")
                        Text(user.cardIdm ?? "")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color.green.opacity(0.1))
                    .cornerRadius(8)
                }
            }
        }
        .sheet(isPresented: $showRegisterFeliCa) {
            RegisterFeliCaView(
                qrToken: user?.qrToken ?? "",
                onSuccess: { idm in
                    // ユーザー情報を再取得
                    fetchUserInfo()
                }
            )
        }
    }

    private func fetchUserInfo() {
        // サーバーからユーザー情報を取得
        // user = ...
    }
}
```

### 2. Info.plistの設定

```xml
<key>NFCReaderUsageDescription</key>
<string>交通系ICカードを登録するためにNFCを使用します</string>
```

### 3. Capabilitiesの設定

1. Xcodeでプロジェクトを開く
2. Signing & Capabilities タブ
3. 「+ Capability」をクリック
4. 「Near Field Communication Tag Reading」を追加

### 4. Entitlementsの設定

```xml
<key>com.apple.developer.nfc.readersession.formats</key>
<array>
    <string>NDEF</string>
    <string>TAG</string>
</array>
```

## API仕様

### POST /link_card

**リクエスト:**
```json
{
  "qr_token": "QR_ABC123...",
  "card_idm": "01010910C21CD521"
}
```

**レスポンス（成功）:**
```json
{
  "status": "ok",
  "message": "カードIDmを紐付けました",
  "card_idm": "01010910C21CD521"
}
```

**レスポンス（失敗）:**
```json
{
  "status": "error",
  "message": "user not found"
}
```

## データモデル

```swift
struct User: Codable {
    let id: Int
    let name: String
    let email: String?
    let balance: Double
    let qrToken: String
    let cardIdm: String?  // FeliCa IDm（登録済みの場合）

    enum CodingKeys: String, CodingKey {
        case id, name, email, balance
        case qrToken = "qr_token"
        case cardIdm = "card_idm"
    }
}
```

## 使用フロー

### 新規ユーザー登録フロー
1. ユーザーアプリで新規登録
2. QRトークンを取得
3. ホーム画面で「FeliCaカードを登録」をタップ
4. Suica/PASMOをiPhoneにかざす
5. IDmが読み取られ、サーバーに送信
6. 登録完了

### 改札利用フロー
1. **QRコード利用**: QRコードを改札のカメラにかざす
2. **FeliCaカード利用**: 登録したSuica/PASMOを改札にタッチ
3. どちらの方法でも同じユーザーとして認証される

## 注意事項

### セキュリティ
- FeliCa IDmは一意であり、他のユーザーと重複しない
- サーバー側で重複チェックが必要（Card.idmのunique制約で対応済み）

### Apple承認について
- FeliCaカードのIDm読み取りは可能
- 残高情報の読み取りにはApple承認が必要な場合がある
- 現在の実装ではIDmのみ使用（承認不要）

### 実機テスト
- NFCは実機でのみ動作（シミュレーターでは不可）
- iPhone 7以降が必要
- 日本国内で販売されたiPhoneが推奨

## トラブルシューティング

### NFCセッションが開始しない
- Capabilitiesが正しく設定されているか確認
- Entitlementsファイルが存在するか確認
- 実機でテストしているか確認

### カードが読み取れない
- iPhoneの背面上部にカードを近づける
- 金属製のケースを外す
- 複数のカードを重ねない

### サーバーエラー
- サーバーURLが正しいか確認
- ネットワーク接続を確認
- サーバーログで詳細を確認

## 参考リンク

- [Apple NFC Documentation](https://developer.apple.com/documentation/corenfc)
- [FeliCa Technical Specification](https://www.sony.co.jp/Products/felica/)
- [TRETJapanNFCReader (参考実装)](https://github.com/treastrain/TRETJapanNFCReader)

## まとめ

この実装により、ユーザーは以下が可能になります：

1. ✅ QRコードで改札を利用
2. ✅ 登録したFeliCaカードで改札を利用
3. ✅ どちらの方法でも同じアカウントの残高を使用
4. ✅ 混合認証（入場はQR、出場はFeliCa等）も可能

改札システム側は既に完成しているので、ユーザーアプリにこの機能を追加すればFeliCa対応が完了します。
