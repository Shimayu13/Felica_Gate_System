//
//  RetailView.swift
//  Felica_Gate_System
//
//  物販モード - 店員が金額を入力してその場で決済
//

import SwiftUI
import AudioToolbox

struct RetailView: View {
    @State private var amount: String = ""
    @State private var resultMessage = ""
    @State private var purchaseResult: PurchaseResult?
    @State private var isProcessing = false
    @State private var clearDisplayToken = UUID()

    @AppStorage("server_url") private var serverURL = "http://Shimayus-MacBook-Pro.local:8000"
    @AppStorage("gate_code") private var gateCode = "STORE_1"

    private var apiClient: APIClient {
        APIClient(baseURL: URL(string: serverURL)!)
    }

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                // 上部：結果表示エリア（2/3の高さ）
                ScrollView {
                    VStack(spacing: 20) {
                        Text("🏪 物販レジ")
                            .font(.title)
                            .fontWeight(.bold)
                            .padding(.top, 20)

                        // 金額入力表示
                        VStack(spacing: 10) {
                            Text("金額")
                                .font(.headline)
                                .foregroundColor(.secondary)

                            Text("¥\(amount.isEmpty ? "0" : amount)")
                                .font(.system(size: 56, weight: .bold, design: .rounded))
                                .foregroundColor(.primary)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(12)
                        }
                        .padding(.horizontal)

                        // 数字キーパッド
                        VStack(spacing: 12) {
                            ForEach([["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]], id: \.self) { row in
                                HStack(spacing: 12) {
                                    ForEach(row, id: \.self) { number in
                                        Button(action: {
                                            appendNumber(number)
                                        }) {
                                            Text(number)
                                                .font(.system(size: 32, weight: .semibold))
                                                .frame(maxWidth: .infinity, minHeight: 70)
                                                .background(Color.blue.opacity(0.1))
                                                .foregroundColor(.primary)
                                                .cornerRadius(10)
                                        }
                                    }
                                }
                            }

                            // 最下行: 00, 0, ←
                            HStack(spacing: 12) {
                                Button(action: {
                                    appendNumber("00")
                                }) {
                                    Text("00")
                                        .font(.system(size: 32, weight: .semibold))
                                        .frame(maxWidth: .infinity, minHeight: 70)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundColor(.primary)
                                        .cornerRadius(10)
                                }

                                Button(action: {
                                    appendNumber("0")
                                }) {
                                    Text("0")
                                        .font(.system(size: 32, weight: .semibold))
                                        .frame(maxWidth: .infinity, minHeight: 70)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundColor(.primary)
                                        .cornerRadius(10)
                                }

                                Button(action: {
                                    deleteLastDigit()
                                }) {
                                    Image(systemName: "delete.left")
                                        .font(.system(size: 28))
                                        .frame(maxWidth: .infinity, minHeight: 70)
                                        .background(Color.red.opacity(0.1))
                                        .foregroundColor(.red)
                                        .cornerRadius(10)
                                }
                            }

                            // クリアボタン
                            Button(action: {
                                clearAmount()
                            }) {
                                Text("クリア")
                                    .font(.headline)
                                    .frame(maxWidth: .infinity, minHeight: 50)
                                    .background(Color.gray.opacity(0.2))
                                    .foregroundColor(.primary)
                                    .cornerRadius(10)
                            }
                        }
                        .padding(.horizontal)

                        // 結果表示
                        if let result = purchaseResult {
                            VStack(spacing: 15) {
                                Image(systemName: "checkmark.circle.fill")
                                    .font(.system(size: 50))
                                    .foregroundColor(.green)

                                Text("決済完了")
                                    .font(.title2)
                                    .fontWeight(.bold)

                                VStack(spacing: 8) {
                                    HStack {
                                        Text("ユーザー:")
                                            .foregroundColor(.secondary)
                                        Spacer()
                                        Text(result.userName)
                                            .fontWeight(.semibold)
                                    }

                                    HStack {
                                        Text("購入金額:")
                                            .foregroundColor(.secondary)
                                        Spacer()
                                        Text("¥\(String(format: "%.0f", result.amount))")
                                            .fontWeight(.semibold)
                                            .foregroundColor(.orange)
                                    }

                                    HStack {
                                        Text("残高:")
                                            .foregroundColor(.secondary)
                                        Spacer()
                                        Text("¥\(String(format: "%.0f", result.balanceAfter))")
                                            .fontWeight(.semibold)
                                    }
                                }
                                .padding()
                                .background(Color.secondary.opacity(0.1))
                                .cornerRadius(10)
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(16)
                            .padding(.horizontal)
                        } else if !resultMessage.isEmpty {
                            // エラーメッセージ
                            VStack(spacing: 15) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.system(size: 50))
                                    .foregroundColor(.red)

                                Text(resultMessage)
                                    .font(.body)
                                    .multilineTextAlignment(.center)
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(12)
                            .foregroundColor(.red)
                            .padding(.horizontal)
                        }

                        Spacer(minLength: 20)
                    }
                }
                .frame(height: geometry.size.height * 2 / 3)
                .background(Color(UIColor.systemBackground))

                Divider()

                // 下部：QRスキャナー（1/3の高さ）
                ZStack {
                    QRScannerView { token in
                        processPurchase(qrToken: token)
                    }
                    .frame(height: geometry.size.height * 1 / 3)

                    // 金額未入力時のオーバーレイ
                    if amount.isEmpty || amount == "0" {
                        Color.black.opacity(0.7)

                        VStack {
                            Image(systemName: "yensign.circle")
                                .font(.system(size: 40))
                                .foregroundColor(.white)

                            Text("金額を入力してください")
                                .foregroundColor(.white)
                                .font(.headline)
                        }
                    }

                    // 処理中のオーバーレイ
                    if isProcessing {
                        Color.black.opacity(0.5)

                        VStack {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(1.5)

                            Text("処理中...")
                                .foregroundColor(.white)
                                .font(.headline)
                                .padding(.top, 10)
                        }
                    }
                }
            }
        }
        .edgesIgnoringSafeArea(.bottom)
    }

    private func appendNumber(_ number: String) {
        // 最大9桁まで
        if amount.count < 9 {
            if amount == "0" {
                amount = number
            } else {
                amount += number
            }
        }
        AudioServicesPlaySystemSound(1104) // キー入力音
    }

    private func deleteLastDigit() {
        if !amount.isEmpty {
            amount.removeLast()
            AudioServicesPlaySystemSound(1104)
        }
    }

    private func clearAmount() {
        amount = ""
        resultMessage = ""
        purchaseResult = nil
        AudioServicesPlaySystemSound(1104)
    }

    private func processPurchase(qrToken: String) {
        guard let amountValue = Double(amount), amountValue > 0 else {
            resultMessage = "金額を入力してください"
            scheduleClearDisplay()
            return
        }

        isProcessing = true
        resultMessage = ""
        purchaseResult = nil
        cancelScheduledClear()

        let request = PurchaseRequest(
            scan_source: "qr",
            qr_token: qrToken,
            amount: amountValue,
            store_code: gateCode,
            device_id: UIDevice.current.identifierForVendor?.uuidString ?? "unknown",
            timestamp: ISO8601DateFormatter().string(from: Date())
        )

        apiClient.postPurchase(request: request) { result in
            DispatchQueue.main.async {
                isProcessing = false

                switch result {
                case .success(let data):
                    handlePurchaseResponse(data)
                case .failure(let error):
                    resultMessage = "ネットワークエラー:\n\(error.localizedDescription)"
                    purchaseResult = nil
                    AudioServicesPlaySystemSound(1006) // エラー音
                    scheduleClearDisplay()
                }
            }
        }
    }

    private func handlePurchaseResponse(_ data: Data) {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

            if let status = json?["status"] as? String, status == "success" {
                let userName = json?["user_name"] as? String ?? "Unknown"
                let amountValue = json?["amount"] as? Double ?? 0
                let balanceAfter = json?["balance_after"] as? Double ?? 0

                purchaseResult = PurchaseResult(
                    userName: userName,
                    amount: amountValue,
                    balanceAfter: balanceAfter
                )
                resultMessage = ""

                AudioServicesPlaySystemSound(1057) // 成功音

                // 金額をクリア
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    clearAmount()
                }

            } else if let status = json?["status"] as? String, status == "error" {
                let message = json?["message"] as? String ?? "不明なエラー"

                if message == "insufficient_balance",
                   let requiredAmount = json?["required_amount"] as? Double,
                   let currentBalance = json?["current_balance"] as? Double {
                    resultMessage = "残高不足\n\n必要金額: ¥\(String(format: "%.0f", requiredAmount))\n現在残高: ¥\(String(format: "%.0f", currentBalance))\n不足額: ¥\(String(format: "%.0f", requiredAmount - currentBalance))"
                } else {
                    resultMessage = "エラー:\n\(translateErrorMessage(message))"
                }

                purchaseResult = nil
                AudioServicesPlaySystemSound(1006) // エラー音
                scheduleClearDisplay()
            } else {
                resultMessage = "不明な応答"
                purchaseResult = nil
                AudioServicesPlaySystemSound(1006)
                scheduleClearDisplay()
            }
        } catch {
            resultMessage = "応答の解析に失敗しました"
            purchaseResult = nil
            AudioServicesPlaySystemSound(1006)
            scheduleClearDisplay()
        }
    }

    private func translateErrorMessage(_ message: String) -> String {
        switch message {
        case "card_not_registered":
            return "このQRコードは登録されていません"
        case "insufficient_balance":
            return "残高が足りません"
        case "user_not_found_for_card":
            return "このカードにユーザーが紐付いていません"
        default:
            return message
        }
    }

    private func scheduleClearDisplay() {
        let token = UUID()
        clearDisplayToken = token

        DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
            if clearDisplayToken == token {
                purchaseResult = nil
                resultMessage = ""
            }
        }
    }

    private func cancelScheduledClear() {
        clearDisplayToken = UUID()
    }
}

struct PurchaseResult {
    let userName: String
    let amount: Double
    let balanceAfter: Double
}

#Preview {
    RetailView()
}
