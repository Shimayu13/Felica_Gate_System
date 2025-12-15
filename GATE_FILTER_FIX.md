# ゲート選択フィルター修正

## 問題

iOSアプリで東京駅を選択しているのに、新宿駅のゲートなど、他の駅のゲートも選択できてしまう問題がありました。

**例**:
- 駅: 東京駅 (JK01)
- ゲート: 新宿駅のゲート ← 本来は選択できないはず

## 原因

[GateSettingsView.swift](Felica_Gate_System/GateSettingsView.swift:76-80)のゲート選択Pickerが、全ゲートリストを表示していました。選択された駅のゲートのみにフィルタリングする処理がありませんでした。

## 修正内容

### 1. フィルタリング用の計算プロパティを追加

[GateSettingsView.swift:21-30](Felica_Gate_System/GateSettingsView.swift#L21-L30)

```swift
// 選択された駅のゲートのみをフィルタリング
private var filteredGates: [Gate] {
    // 選択された駅のIDを取得
    guard let selectedStation = stations.first(where: { $0.code == stationCode }) else {
        return gates
    }

    // 選択された駅のゲートのみを返す
    return gates.filter { $0.station_id == selectedStation.id }
}
```

**動作**:
1. 現在選択されている駅コード（`stationCode`）から駅情報を取得
2. 取得した駅のID（`selectedStation.id`）に一致するゲートのみをフィルタ
3. 駅が見つからない場合は全ゲートを返す（フォールバック）

### 2. ゲートPickerを修正

[GateSettingsView.swift:76-80](Felica_Gate_System/GateSettingsView.swift#L76-L80)

**修正前**:
```swift
Picker("ゲート", selection: $gateCode) {
    ForEach(gates, id: \.code) { gate in
        Text("\(gate.name) (\(gate.code))").tag(gate.code)
    }
}
```

**修正後**:
```swift
Picker("ゲート", selection: $gateCode) {
    ForEach(filteredGates, id: \.code) { gate in
        Text("\(gate.name) (\(gate.code))").tag(gate.code)
    }
}
```

変更点: `gates` → `filteredGates`

### 3. 警告メッセージを追加

[GateSettingsView.swift:85-89](Felica_Gate_System/GateSettingsView.swift#L85-L89)

```swift
if filteredGates.isEmpty && !stations.isEmpty {
    Text("選択された駅にゲートがありません")
        .foregroundColor(.orange)
        .font(.caption)
}
```

選択された駅にゲートが存在しない場合、ユーザーに警告を表示します。

## 動作確認

### テストケース1: 東京駅を選択

1. 駅Pickerで「東京 (JK01)」を選択
2. ゲートPickerには以下のみが表示される:
   - 東京 入口 (JK01_IN)
   - 東京 出口 (JK01_OUT)
3. 新宿駅や他の駅のゲートは表示されない ✅

### テストケース2: 横浜駅を選択

1. 駅Pickerで「横浜 (JK15)」を選択
2. ゲートPickerには以下のみが表示される:
   - 横浜 入口 (JK15_IN)
   - 横浜 出口 (JK15_OUT)

### テストケース3: ゲートが存在しない駅

1. 新しい駅を手動入力（ゲート未登録）
2. 警告メッセージが表示される: 「選択された駅にゲートがありません」
3. 手動入力フィールドは引き続き使用可能

### テストケース4: 駅変更時の自動更新

1. 駅Aを選択 → 駅AのゲートA1を選択
2. 駅Bに変更
3. ゲートPickerが駅Bのゲートのみに自動更新される
4. `gateCode`の値は保持されるが、Pickerには駅Bのゲートのみ表示

## データ構造

### Station Model
```swift
struct Station: Codable {
    let id: Int           // データベースの主キー
    let code: String      // 駅コード (例: "JK01")
    let name: String      // 駅名 (例: "東京")
}
```

### Gate Model
```swift
struct Gate: Codable {
    let id: Int           // データベースの主キー
    let code: String      // ゲートコード (例: "JK01_IN")
    let station_id: Int?  // 所属する駅のID（これでフィルタリング）
    let name: String      // ゲート名 (例: "東京 入口")
}
```

フィルタリングは `gate.station_id == selectedStation.id` で行います。

## データベースの対応関係

```
stations テーブル:
+----+------+--------+
| id | code | name   |
+----+------+--------+
| 4  | JK01 | 東京   |
| 5  | JK02 | 有楽町 |
+----+------+--------+

gates テーブル:
+----+----------+------------+--------------+
| id | code     | station_id | name         |
+----+----------+------------+--------------+
| 4  | JK01_IN  | 4          | 東京 入口    |
| 5  | JK01_OUT | 4          | 東京 出口    |
| 6  | JK02_IN  | 5          | 有楽町 入口  |
| 7  | JK02_OUT | 5          | 有楽町 出口  |
+----+----------+------------+--------------+
```

東京駅（id=4）を選択した場合、`station_id=4`のゲートのみ表示されます。

## アプリのビルドと実行

### Xcodeでビルド

1. Xcodeで `Felica_Gate_System.xcodeproj` を開く
2. シミュレーターまたは実機を選択
3. ⌘+R でビルド＆実行

### 確認手順

1. アプリ起動後、「改札機設定」タブを開く
2. 「駅・ゲート情報を取得」ボタンをタップ
3. サーバーから駅とゲートの情報を取得
4. 駅Pickerで任意の駅を選択
5. ゲートPickerに選択した駅のゲートのみが表示されることを確認

## フォールバック機能

手動入力フィールドは引き続き使用可能です:

1. **駅コード（手動入力）**: Pickerにない駅を直接入力可能
2. **ゲートコード（手動入力）**: Pickerにないゲートを直接入力可能

これにより、以下のケースでも対応可能:
- サーバーから情報が取得できない場合
- データベースに未登録の駅・ゲートを使用する場合
- オフラインでの設定変更

## まとめ

✅ **駅選択に基づくゲートフィルタリング**
- 選択した駅のゲートのみがPickerに表示される
- 他の駅のゲートは選択できない

✅ **リアルタイム更新**
- 駅を変更すると、ゲートPickerも自動的に更新される

✅ **ユーザーフレンドリー**
- ゲートがない場合は警告メッセージを表示
- 手動入力フィールドはフォールバックとして機能

✅ **データ整合性**
- 駅とゲートの関連性が正しく維持される
- 誤った組み合わせでの設定を防止

---

**修正完了日**: 2025年12月14日
