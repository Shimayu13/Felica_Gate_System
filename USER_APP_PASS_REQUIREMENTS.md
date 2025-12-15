# ユーザーアプリ：定期券機能実装要件

## 概要

ユーザーアプリに定期券の確認・表示機能を追加してください。ユーザーが自分の定期券情報を確認し、有効期限や区間を把握できるようにします。

---

## 実装する機能

### 1. 定期券一覧表示画面

**画面名:** PassListView

**表示内容:**
- ユーザーが持つ定期券の一覧
- 各定期券カードに以下の情報を表示:
  - 定期券種別（通勤定期 / 通学定期）
  - 区間（例: 東京駅 → 新宿駅）
  - 有効期間（例: 2025/12/01 - 2026/02/28）
  - 残り日数（例: あと75日）
  - 有効 / 無効の状態

**デザイン要件:**
- カード型のUI
- 有効な定期券は緑色のアクセントカラー
- 期限切れ・無効な定期券はグレー表示
- 残り日数が30日未満の場合は黄色で警告表示
- 残り日数が7日未満の場合は赤色で警告表示

**UIイメージ:**
```
┌────────────────────────────────┐
│ 🎫 通勤定期                     │
│                                │
│ 東京駅 ⟷ 新宿駅               │
│                                │
│ 有効期間                        │
│ 2025/12/01 - 2026/02/28       │
│                                │
│ 🟢 有効 (あと75日)             │
└────────────────────────────────┘
```

---

### 2. 定期券詳細表示

**画面名:** PassDetailView

**表示内容:**
- 定期券ID
- 種別（通勤 / 通学）
- 区間（駅名表示、駅コードも併記）
- 有効期間（開始日時・終了日時）
- 残り日数
- 作成日時
- 状態（有効 / 無効）

**機能:**
- 定期券のQRコード表示（定期券IDをQRコード化）
- 区間の地図表示（オプション）

---

### 3. APIエンドポイント統合

**使用するエンドポイント:**

#### GET /users/{user_id}/passes
ユーザーの定期券一覧を取得

**リクエスト例:**
```swift
let url = URL(string: "http://localhost:8000/users/3/passes?active_only=true")!
var request = URLRequest(url: url)
request.httpMethod = "GET"

URLSession.shared.dataTask(with: request) { data, response, error in
    // レスポンス処理
}.resume()
```

**レスポンス例:**
```json
[
  {
    "id": 1,
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "ST01",
    "station_to": "ST02",
    "valid_from": "2025-12-01T00:00:00",
    "valid_until": "2026-02-28T23:59:59",
    "is_active": 1,
    "created_at": "2025-12-14T01:36:03.346305"
  }
]
```

#### GET /passes/{pass_id}
特定の定期券詳細を取得

**リクエスト例:**
```swift
let url = URL(string: "http://localhost:8000/passes/1")!
var request = URLRequest(url: url)
request.httpMethod = "GET"

URLSession.shared.dataTask(with: request) { data, response, error in
    // レスポンス処理
}.resume()
```

---

### 4. データモデル

**Pass.swift を作成:**
```swift
import Foundation

struct Pass: Codable, Identifiable {
    let id: Int
    let user_id: Int
    let pass_type: String  // "commuter" or "student"
    let station_from: String
    let station_to: String
    let valid_from: String  // ISO 8601形式
    let valid_until: String // ISO 8601形式
    let is_active: Int      // 1=有効, 0=無効
    let created_at: String

    // 計算プロパティ
    var isValid: Bool {
        guard is_active == 1 else { return false }

        let formatter = ISO8601DateFormatter()
        guard let validUntil = formatter.date(from: valid_until) else {
            return false
        }

        return validUntil > Date()
    }

    var daysRemaining: Int {
        let formatter = ISO8601DateFormatter()
        guard let validUntil = formatter.date(from: valid_until) else {
            return 0
        }

        let calendar = Calendar.current
        let components = calendar.dateComponents([.day], from: Date(), to: validUntil)
        return max(0, components.day ?? 0)
    }

    var passTypeName: String {
        switch pass_type {
        case "commuter":
            return "通勤定期"
        case "student":
            return "通学定期"
        default:
            return "定期券"
        }
    }

    var validPeriodText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy/MM/dd"
        formatter.locale = Locale(identifier: "ja_JP")

        let isoFormatter = ISO8601DateFormatter()

        guard let fromDate = isoFormatter.date(from: valid_from),
              let toDate = isoFormatter.date(from: valid_until) else {
            return "不明"
        }

        return "\(formatter.string(from: fromDate)) - \(formatter.string(from: toDate))"
    }
}
```

---

### 5. API通信クラスの拡張

**既存のAPIClient.swiftに以下のメソッドを追加:**

```swift
// ユーザーの定期券一覧を取得
func getUserPasses(userId: Int, activeOnly: Bool = true, completion: @escaping (Result<Data, Error>) -> Void) {
    let urlString = "\(baseURL)/users/\(userId)/passes?active_only=\(activeOnly)"
    guard let url = URL(string: urlString) else { return }

    var request = URLRequest(url: url)
    request.httpMethod = "GET"

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(.failure(error))
            return
        }

        if let data = data {
            completion(.success(data))
        }
    }.resume()
}

// 定期券詳細を取得
func getPass(passId: Int, completion: @escaping (Result<Data, Error>) -> Void) {
    let urlString = "\(baseURL)/passes/\(passId)"
    guard let url = URL(string: urlString) else { return }

    var request = URLRequest(url: url)
    request.httpMethod = "GET"

    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(.failure(error))
            return
        }

        if let data = data {
            completion(.success(data))
        }
    }.resume()
}
```

---

### 6. PassListView の実装例

```swift
import SwiftUI

struct PassListView: View {
    @State private var passes: [Pass] = []
    @State private var isLoading = false
    @State private var errorMessage = ""

    let userId: Int
    let apiClient: APIClient

    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("読み込み中...")
                } else if !errorMessage.isEmpty {
                    VStack {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 50))
                            .foregroundColor(.orange)
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .padding()
                    }
                } else if passes.isEmpty {
                    VStack {
                        Image(systemName: "ticket")
                            .font(.system(size: 80))
                            .foregroundColor(.gray)
                        Text("定期券がありません")
                            .foregroundColor(.secondary)
                            .padding()
                    }
                } else {
                    List(passes) { pass in
                        NavigationLink(destination: PassDetailView(pass: pass)) {
                            PassCardView(pass: pass)
                        }
                    }
                }
            }
            .navigationTitle("定期券")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: loadPasses) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
        }
        .onAppear {
            loadPasses()
        }
    }

    private func loadPasses() {
        isLoading = true
        errorMessage = ""

        apiClient.getUserPasses(userId: userId, activeOnly: false) { result in
            DispatchQueue.main.async {
                isLoading = false

                switch result {
                case .success(let data):
                    do {
                        let decoder = JSONDecoder()
                        passes = try decoder.decode([Pass].self, from: data)
                    } catch {
                        errorMessage = "データの解析に失敗しました"
                    }
                case .failure(let error):
                    errorMessage = "定期券の取得に失敗しました\n\(error.localizedDescription)"
                }
            }
        }
    }
}

struct PassCardView: View {
    let pass: Pass

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(pass.passTypeName)
                    .font(.headline)
                Spacer()
                StatusBadge(pass: pass)
            }

            HStack {
                Text(stationName(pass.station_from))
                Image(systemName: "arrow.left.arrow.right")
                    .foregroundColor(.secondary)
                Text(stationName(pass.station_to))
            }
            .font(.title3)

            Text(pass.validPeriodText)
                .font(.caption)
                .foregroundColor(.secondary)

            if pass.isValid {
                Text("あと\(pass.daysRemaining)日")
                    .font(.caption)
                    .foregroundColor(daysColor(pass.daysRemaining))
            }
        }
        .padding()
        .background(pass.isValid ? Color.green.opacity(0.1) : Color.gray.opacity(0.1))
        .cornerRadius(12)
    }

    private func stationName(_ code: String) -> String {
        // TODO: 駅コードから駅名を取得するロジック
        return code
    }

    private func daysColor(_ days: Int) -> Color {
        if days < 7 {
            return .red
        } else if days < 30 {
            return .orange
        } else {
            return .green
        }
    }
}

struct StatusBadge: View {
    let pass: Pass

    var body: some View {
        HStack {
            Circle()
                .fill(pass.isValid ? Color.green : Color.gray)
                .frame(width: 8, height: 8)
            Text(pass.isValid ? "有効" : "無効")
                .font(.caption)
                .foregroundColor(pass.isValid ? .green : .gray)
        }
    }
}
```

---

### 7. 駅名マスターの統合

**オプション機能:**
サーバーから駅情報を取得して、駅コードを駅名に変換する機能を追加してください。

**エンドポイント:** `GET /stations`

**使用例:**
```swift
struct Station: Codable {
    let id: Int
    let code: String
    let name: String
}

class StationCache {
    static let shared = StationCache()
    private var stations: [String: String] = [:]  // [code: name]

    func loadStations(apiClient: APIClient) {
        // GET /stations を呼び出して駅情報を取得
        // stations辞書に格納
    }

    func stationName(for code: String) -> String {
        return stations[code] ?? code
    }
}
```

---

## 実装手順

1. **Pass.swift データモデルを作成**
   - 定期券の構造体を定義
   - 計算プロパティで残り日数や有効性を判定

2. **APIClient.swift を拡張**
   - `getUserPasses()` メソッドを追加
   - `getPass()` メソッドを追加

3. **PassListView.swift を作成**
   - 定期券一覧を表示
   - カード型のUI
   - 状態に応じた色分け

4. **PassDetailView.swift を作成**
   - 定期券の詳細情報を表示
   - QRコード表示機能（オプション）

5. **メインアプリに統合**
   - タブビューまたはメニューに「定期券」を追加
   - ログイン後のユーザー情報からuser_idを取得

---

## テスト方法

### 1. テスト用定期券を作成
```bash
curl -X POST "http://localhost:8000/passes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "pass_type": "commuter",
    "station_from": "ST01",
    "station_to": "ST02",
    "valid_from": "2025-12-01T00:00:00Z",
    "valid_until": "2026-02-28T23:59:59Z"
  }'
```

### 2. アプリで確認
- ユーザーアプリを起動
- ログイン
- 「定期券」タブを開く
- 作成した定期券が表示されることを確認
- 有効期限や残り日数が正しく表示されることを確認

### 3. 期限切れ定期券のテスト
```bash
# 期限切れの定期券を作成
curl -X POST "http://localhost:8000/passes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "pass_type": "student",
    "station_from": "ST02",
    "station_to": "ST03",
    "valid_from": "2024-01-01T00:00:00Z",
    "valid_until": "2024-03-31T23:59:59Z"
  }'
```

---

## 追加機能（オプション）

### 1. 定期券の更新通知
- 有効期限が近づいたらプッシュ通知
- 残り7日、3日、1日で通知

### 2. 定期券購入機能
- アプリ内で新しい定期券を購入
- 支払い処理（モック）
- POST /passes エンドポイントを使用

### 3. 利用統計
- 定期券を使った乗車回数を表示
- コスト削減効果を計算
- グラフで表示

---

## 注意事項

1. **日付フォーマット**: サーバーからのレスポンスはISO 8601形式（例: "2025-12-01T00:00:00"）です。日本語表示に変換する際は DateFormatter を使用してください。

2. **タイムゾーン**: サーバーはUTCで時刻を管理しています。ローカルタイムゾーンへの変換が必要な場合は適切に処理してください。

3. **エラーハンドリング**: ネットワークエラーやデータ解析エラーに対して適切なエラーメッセージを表示してください。

4. **リフレッシュ機能**: 定期券一覧はキャッシュせず、画面表示時に毎回サーバーから最新情報を取得してください。

---

## サーバー側の対応状況

✅ すべての必要なAPIエンドポイントは実装済みです
- GET /users/{user_id}/passes
- GET /passes
- GET /passes/{pass_id}
- POST /passes（管理者用）
- PATCH /passes/{pass_id}/deactivate（管理者用）

✅ データベーステーブルも作成済みです
- passes テーブル
- trips.used_pass_id カラム

✅ 改札機アプリでの定期券自動適用も実装済みです
- 出場時に自動的に定期券をチェック
- 有効な定期券があれば運賃0円

---

以上の要件に従って、ユーザーアプリに定期券機能を実装してください。
