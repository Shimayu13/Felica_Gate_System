# ユーザーアプリ - 顔認証機能実装プロンプト

## 概要

ユーザーアプリに顔認証登録機能を追加してください。ユーザーが自分の顔を登録できるようにすることで、改札で顔認証を使って入退場できるようになります。

## 現在の状態

### サーバー側（完成済み）
- ✅ **POST /face/register/upload** - 顔登録API（ファイルアップロード版）
  - パラメータ: `user_id` (整数), `file` (顔画像ファイル)
  - レスポンス: 登録成功/失敗
- ✅ **POST /face/verify/upload** - 顔認証API
  - パラメータ: `file` (顔画像ファイル)
  - レスポンス: 認証結果、ユーザー情報、残高

### 改札アプリ側（完成済み）
- ✅ 顔認証モードの追加
- ✅ FaceCameraView（カメラキャプチャビュー）
- ✅ 顔認証API連携
- ✅ 認証結果の表示

### ユーザーアプリ側（未実装）
- ❌ 顔登録機能
- ❌ 登録済み顔の管理（確認・再登録・削除）

## 実装してほしい機能

### 1. 顔登録画面（FaceRegistrationView）

**場所**: 設定画面またはプロフィール画面から遷移

**UI構成**:
```
┌─────────────────────────────────┐
│  顔認証設定                      │
├─────────────────────────────────┤
│                                  │
│  ┌────────────────────┐        │
│  │                    │         │
│  │   顔アイコン        │         │
│  │  （登録済み/未登録）│         │
│  └────────────────────┘        │
│                                  │
│  ステータス:                     │
│  [✓ 登録済み] または [未登録]    │
│                                  │
│  ┌─────────────────────┐       │
│  │  顔を登録/再登録       │       │
│  └─────────────────────┘       │
│                                  │
│  ┌─────────────────────┐       │
│  │  登録を解除            │       │
│  └─────────────────────┘       │
│                                  │
│  ℹ️ 顔認証について                │
│  ・改札で顔認証が使えます        │
│  ・QRコードも引き続き使えます    │
└─────────────────────────────────┘
```

**機能**:
1. **登録ボタンタップ**:
   - FaceCaptureView（カメラビュー）を全画面表示
   - 顔を撮影
   - サーバーに送信して登録

2. **再登録ボタン**:
   - 既に登録済みの場合は確認ダイアログを表示
   - 同意後、新しい顔を撮影して上書き登録

3. **登録解除ボタン**:
   - 確認ダイアログを表示
   - サーバー側の顔データを無効化（is_active = 0）

### 2. FaceCaptureView（カメラビュー）の再利用

**重要**: 改札アプリの `FaceCaptureView.swift` をそのまま使用してください。

**使い方**:
```swift
import SwiftUI

struct FaceRegistrationView: View {
    @State private var showCamera = false
    @State private var isRegistered = false
    @State private var registrationMessage = ""

    var body: some View {
        VStack(spacing: 20) {
            // ステータス表示
            Image(systemName: isRegistered ? "checkmark.circle.fill" : "person.crop.circle.badge.questionmark")
                .font(.system(size: 80))
                .foregroundColor(isRegistered ? .green : .gray)

            Text(isRegistered ? "登録済み" : "未登録")
                .font(.title2)
                .fontWeight(.semibold)

            if !registrationMessage.isEmpty {
                Text(registrationMessage)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }

            // 登録ボタン
            Button(action: { showCamera = true }) {
                HStack {
                    Image(systemName: "camera.fill")
                    Text(isRegistered ? "顔を再登録" : "顔を登録")
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.blue)
                .cornerRadius(12)
            }
            .padding(.horizontal)

            // 登録解除ボタン（登録済みの場合のみ）
            if isRegistered {
                Button(action: unregisterFace) {
                    Text("登録を解除")
                        .font(.headline)
                        .foregroundColor(.red)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(12)
                }
                .padding(.horizontal)
            }

            // 説明
            VStack(alignment: .leading, spacing: 8) {
                Label("改札で顔認証が使えます", systemImage: "faceid")
                Label("QRコードも引き続き使えます", systemImage: "qrcode")
                Label("顔画像は暗号化して保存されます", systemImage: "lock.shield")
            }
            .font(.caption)
            .foregroundColor(.secondary)
            .padding()
            .background(Color.blue.opacity(0.05))
            .cornerRadius(12)
            .padding(.horizontal)

            Spacer()
        }
        .padding(.top, 40)
        .navigationTitle("顔認証設定")
        .fullScreenCover(isPresented: $showCamera) {
            FaceCameraView(
                onCapture: { image in
                    showCamera = false
                    registerFace(image: image)
                },
                onCancel: {
                    showCamera = false
                }
            )
        }
        .onAppear {
            checkRegistrationStatus()
        }
    }

    private func registerFace(image: UIImage) {
        registrationMessage = "登録中..."

        // TODO: APIClient に postFaceRegister メソッドを追加
        // APIClient().postFaceRegister(userId: currentUserId, faceImage: image) { result in
        //     DispatchQueue.main.async {
        //         switch result {
        //         case .success:
        //             isRegistered = true
        //             registrationMessage = "顔の登録が完了しました"
        //         case .failure(let error):
        //             registrationMessage = "登録に失敗しました: \(error.localizedDescription)"
        //         }
        //     }
        // }
    }

    private func unregisterFace() {
        // 確認ダイアログを表示してから解除
        // TODO: サーバーのis_activeを0にするAPIを呼び出す
    }

    private func checkRegistrationStatus() {
        // TODO: サーバーから登録状態を確認
        // GET /face/status/{user_id} などのエンドポイントを追加するか、
        // ユーザー情報に face_registered フラグを追加
    }
}
```

### 3. APIClient の拡張

**追加するメソッド**:

```swift
// APIClient.swift に追加

func postFaceRegister(userId: Int, faceImage: UIImage, completion: @escaping (Result<Data, Error>) -> Void) {
    let url = baseURL.appendingPathComponent("face/register/upload")

    var urlRequest = URLRequest(url: url)
    urlRequest.httpMethod = "POST"

    // マルチパートフォームデータを構築
    let boundary = UUID().uuidString
    urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

    guard let imageData = faceImage.jpegData(compressionQuality: 0.8) else {
        completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to convert image to JPEG"])))
        return
    }

    var body = Data()

    // user_id フィールドを追加
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"user_id\"\r\n\r\n".data(using: .utf8)!)
    body.append("\(userId)\r\n".data(using: .utf8)!)

    // file フィールドを追加
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"face.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n".data(using: .utf8)!)
    body.append("--\(boundary)--\r\n".data(using: .utf8)!)

    urlRequest.httpBody = body

    let task = URLSession.shared.dataTask(with: urlRequest) { data, response, error in
        if let error = error {
            completion(.failure(error))
            return
        }

        guard let data = data else {
            completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
            return
        }

        completion(.success(data))
    }

    task.resume()
}
```

### 4. ナビゲーション統合

**設定画面またはプロフィール画面に追加**:

```swift
NavigationLink(destination: FaceRegistrationView()) {
    HStack {
        Image(systemName: "faceid")
            .foregroundColor(.blue)
            .frame(width: 30)

        Text("顔認証設定")

        Spacer()

        // 登録状態のバッジ
        if isFaceRegistered {
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.green)
        }

        Image(systemName: "chevron.right")
            .foregroundColor(.secondary)
            .font(.caption)
    }
    .padding()
    .background(Color.gray.opacity(0.1))
    .cornerRadius(12)
}
```

## サーバーAPI仕様

### POST /face/register/upload

**リクエスト**: Form-data形式
- `user_id`: ユーザーID（整数）
- `file`: 顔画像ファイル（JPEG/PNG/HEIC）

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "顔の登録に成功しました",
  "user_id": 3,
  "user_name": "山田太郎",
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

### 追加が必要なエンドポイント（サーバー側）

以下のエンドポイントは現時点で未実装です。必要に応じてサーバー開発者に依頼してください：

1. **GET /face/status/{user_id}** - 顔登録状態の確認
   ```json
   {
     "user_id": 3,
     "is_registered": true,
     "registered_at": "2025-12-22T10:30:00Z"
   }
   ```

2. **DELETE /face/{user_id}** - 顔登録の削除（is_activeを0にする）
   ```json
   {
     "status": "success",
     "message": "顔データを削除しました"
   }
   ```

## 実装チェックリスト

- [ ] FaceCaptureView.swift を改札アプリからコピー
- [ ] FaceRegistrationView.swift を作成
- [ ] APIClient に postFaceRegister メソッドを追加
- [ ] 設定画面/プロフィール画面にナビゲーションリンクを追加
- [ ] 顔登録状態の確認機能を実装
- [ ] 登録解除機能を実装
- [ ] エラーハンドリングとユーザーフィードバックを実装
- [ ] カメラ権限のリクエストを処理
- [ ] テスト: 新規登録、再登録、削除の動作確認

## 注意事項

1. **カメラ権限**: Info.plist に `NSCameraUsageDescription` を追加済みか確認
2. **HEIC対応**: iPhoneで撮影した画像はHEIC形式の可能性あり（サーバー側で対応済み）
3. **セキュリティ**: 顔画像は一時的にのみ保存され、特徴量のみがデータベースに保存されます
4. **UX**: 登録時は明るい場所で、正面を向いて撮影するよう案内を表示
5. **エラーハンドリング**: ネットワークエラー、顔検出失敗など、様々なエラーケースに対応

## 参考ファイル

改札アプリ側の実装を参考にしてください：

- `/Users/yuki/Developer/Felica_Gate_System/Felica_Gate_System/FaceCameraView.swift` - カメラビュー
- `/Users/yuki/Developer/Felica_Gate_System/Felica_Gate_System/ContentView.swift` - 顔認証の使用例
- `/Users/yuki/Developer/Felica_Gate_System/Felica_Gate_System/APIClient.swift` - API連携（postFaceVerify メソッド参照）
- `/Users/yuki/Developer/Felica_Gate_System/FACE_RECOGNITION_API.md` - API仕様書

## サポートが必要な場合

質問や不明点があれば、以下の情報を提供してください：
- エラーメッセージ
- 再現手順
- 期待する動作と実際の動作

実装頑張ってください！
