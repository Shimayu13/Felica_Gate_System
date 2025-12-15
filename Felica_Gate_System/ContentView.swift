//
//  ContentView.swift
//  Felica_Gate_System
//
//  Created by Yuki Shimazu on 2025/12/11.
//

import SwiftUI
import AVFoundation
import AudioToolbox

struct ContentView: View {
    @State private var selectedTab = 0
    @AppStorage("gate_mode") private var gateMode = "transit"  // transit or retail

    var body: some View {
        TabView(selection: $selectedTab) {
            // モードに応じてビューを切り替え
            if gateMode == "transit" {
                GateView()
                    .tabItem {
                        Label("改札スキャン", systemImage: "qrcode.viewfinder")
                    }
                    .tag(0)
            } else {
                RetailView()
                    .tabItem {
                        Label("物販レジ", systemImage: "creditcard")
                    }
                    .tag(0)
            }

            GateSettingsView()
                .tabItem {
                    Label("設定", systemImage: "gear")
                }
                .tag(1)
        }
    }
}

struct GateView: View {
    @State private var resultMessage = ""
    @State private var scanResult: ScanResult?
    @State private var isProcessing = false
    @State private var clearDisplayToken = UUID()

    @AppStorage("station_code") private var stationCode = "STATION_1"
    @AppStorage("gate_code") private var gateCode = "STATION_1_IN"
    @AppStorage("server_url") private var serverURL = "http://Shimayus-MacBook-Pro.local:8000"

    private var apiClient: APIClient {
        APIClient(baseURL: URL(string: serverURL)!)
    }

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                // 上部：ユーザー情報表示エリア（2/3の高さ）
                ScrollView {
                    VStack(spacing: 20) {
                        Text("FeliCa Gate System")
                            .font(.title)
                            .fontWeight(.bold)
                            .padding(.top, 20)

                        // 結果表示エリア
                        if let result = scanResult {
                            VStack(spacing: 20) {
                                // 入場/出場アイコンと表示
                                HStack(spacing: 20) {
                                    Image(systemName: result.mode == "entry" ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                                        .font(.system(size: 60))
                                        .foregroundColor(result.mode == "entry" ? .green : .blue)

                                    VStack(alignment: .leading, spacing: 5) {
                                        Text(result.mode == "entry" ? "入場しました" : "出場しました")
                                            .font(.title2)
                                            .fontWeight(.bold)

                                        if let station = result.stationCode, let gate = result.gateCode {
                                            HStack {
                                                Image(systemName: "building.2.fill")
                                                    .foregroundColor(.secondary)
                                                Text("\(station) / \(gate)")
                                                    .font(.subheadline)
                                                    .foregroundColor(.secondary)
                                            }
                                        }
                                    }

                                    Spacer()
                                }

                                Divider()

                                // ユーザー情報
                                if let userName = result.userName {
                                    HStack {
                                        Image(systemName: "person.circle.fill")
                                            .font(.system(size: 40))
                                            .foregroundColor(.blue)

                                        Text(userName)
                                            .font(.title2)
                                            .fontWeight(.semibold)

                                        Spacer()
                                    }
                                }

                                // 残高表示
                                if let balance = result.balance {
                                    VStack(spacing: 8) {
                                        HStack {
                                            Text("残高")
                                                .font(.headline)
                                                .foregroundColor(.secondary)
                                            Spacer()
                                        }

                                        HStack {
                                            Text("¥\(String(format: "%.0f", balance))")
                                                .font(.system(size: 48, weight: .bold, design: .rounded))
                                                .foregroundColor(balance < 1000 ? .red : .primary)

                                            Spacer()
                                        }
                                    }
                                    .padding()
                                    .frame(maxWidth: .infinity)
                                    .background(Color.blue.opacity(0.05))
                                    .cornerRadius(12)
                                }

                                // 利用金額表示（将来的な準備）
                                if let usageAmount = result.usageAmount {
                                    VStack(spacing: 8) {
                                        HStack {
                                            Text("利用金額")
                                                .font(.headline)
                                                .foregroundColor(.secondary)
                                            Spacer()
                                        }

                                        HStack {
                                            Text("¥\(String(format: "%.0f", usageAmount))")
                                                .font(.system(size: 36, weight: .semibold, design: .rounded))
                                                .foregroundColor(.orange)

                                            Spacer()
                                        }
                                    }
                                    .padding()
                                    .frame(maxWidth: .infinity)
                                    .background(Color.orange.opacity(0.05))
                                    .cornerRadius(12)
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.secondary.opacity(0.05))
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
                        } else {
                            // 初期状態
                            VStack(spacing: 15) {
                                Image(systemName: "qrcode.viewfinder")
                                    .font(.system(size: 80))
                                    .foregroundColor(.gray)

                                Text("QRコードをスキャンしてください")
                                    .font(.title3)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                            .frame(maxWidth: .infinity, minHeight: 250)
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
                        sendScan(qrToken: token)
                    }
                    .frame(height: geometry.size.height * 1 / 3)

                    // スキャン中のオーバーレイ
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

    private func sendScan(qrToken: String) {
        isProcessing = true
        resultMessage = ""
        scanResult = nil
        cancelScheduledClear()

        let request = ScanRequest(
            scan_source: "qr",
            card_idm: nil,
            qr_token: qrToken,
            station_code: stationCode,
            gate_code: gateCode,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            device_id: UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
        )

        apiClient.postScan(request: request) { result in
            DispatchQueue.main.async {
                isProcessing = false

                switch result {
                case .success(let data):
                    handleScanResponse(data, qrToken: qrToken)
                case .failure(let error):
                    resultMessage = "ネットワークエラー:\n\(error.localizedDescription)"
                    scanResult = nil
                    scheduleClearDisplay()
                }
            }
        }
    }

    private func handleScanResponse(_ data: Data, qrToken: String) {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

            if let mode = json?["mode"] as? String {
                let usageAmount = json?["usage_amount"] as? Double
                let balanceAfterScan = json?["balance"] as? Double
                let userId = json?["user_id"] as? Int

                GateSound.playSuccess()

                // 成功 - ユーザー情報を取得
                fetchUserInfo(
                    qrToken: qrToken,
                    mode: mode,
                    usageAmount: usageAmount,
                    balanceOverride: balanceAfterScan,
                    userIdHint: userId
                )
            } else if let status = json?["status"] as? String, status == "error" {
                let message = json?["message"] as? String ?? "不明なエラー"

                // 残高不足エラーの場合は詳細情報を表示
                if message == "insufficient_balance",
                   let requiredFare = json?["required_fare"] as? Double,
                   let currentBalance = json?["current_balance"] as? Double {
                    resultMessage = "残高不足で出場できません\n\n必要運賃: ¥\(String(format: "%.0f", requiredFare))\n現在残高: ¥\(String(format: "%.0f", currentBalance))\n不足額: ¥\(String(format: "%.0f", requiredFare - currentBalance))"
                    GateSound.playError()
                } else {
                    resultMessage = "エラー:\n\(translateErrorMessage(message))"
                }
                scanResult = nil
                scheduleClearDisplay()
            } else {
                resultMessage = "不明な応答"
                scanResult = nil
                scheduleClearDisplay()
            }
        } catch {
            resultMessage = "応答の解析に失敗しました"
            scanResult = nil
            scheduleClearDisplay()
        }
    }

    private func fetchUserInfo(qrToken: String, mode: String, usageAmount: Double? = nil, balanceOverride: Double? = nil, userIdHint: Int? = nil) {
        // カード情報からユーザー情報を取得
        if let userIdHint = userIdHint {
            fetchUserDetails(
                userId: userIdHint,
                mode: mode,
                usageAmount: usageAmount,
                balanceOverride: balanceOverride
            )
            return
        }

        apiClient.getCards { result in
            switch result {
            case .success(let data):
                do {
                    let json = try JSONSerialization.jsonObject(with: data) as? [[String: Any]]
                    if let card = json?.first(where: { $0["qr_token"] as? String == qrToken }),
                       let userId = card["user_id"] as? Int {
                        fetchUserDetails(
                            userId: userId,
                            mode: mode,
                            usageAmount: usageAmount,
                            balanceOverride: balanceOverride
                        )
                    } else {
                        DispatchQueue.main.async {
                            resultMessage = "カード情報が見つかりません"
                            scheduleClearDisplay()
                        }
                    }
                } catch {
                    DispatchQueue.main.async {
                        resultMessage = "カード情報の解析に失敗"
                        scheduleClearDisplay()
                    }
                }
            case .failure:
                DispatchQueue.main.async {
                    resultMessage = "カード情報の取得に失敗"
                    scheduleClearDisplay()
                }
            }
        }
    }

    private func fetchUserDetails(userId: Int, mode: String, usageAmount: Double? = nil, balanceOverride: Double? = nil) {
        apiClient.getUser(userId: userId) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let data):
                    do {
                        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                        let userName = json?["name"] as? String
                        let balance = json?["balance"] as? Double

                        scanResult = ScanResult(
                            mode: mode,
                            userName: userName,
                            balance: balanceOverride ?? balance,
                            stationCode: stationCode,
                            gateCode: gateCode,
                            usageAmount: usageAmount
                        )
                        resultMessage = ""
                        scheduleClearDisplay()
                    } catch {
                        resultMessage = "ユーザー情報の解析に失敗"
                        scheduleClearDisplay()
                    }
                case .failure:
                    resultMessage = "ユーザー情報の取得に失敗"
                    scheduleClearDisplay()
                }
            }
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
                scanResult = nil
                resultMessage = ""
            }
        }
    }

    private func cancelScheduledClear() {
        clearDisplayToken = UUID()
    }
}

private enum GateSound {
    static func playSuccess() {
        // 軽い通知音
        AudioServicesPlaySystemSound(1057)
    }

    static func playError() {
        // 短い警告音
        AudioServicesPlaySystemSound(1006)
    }
}

struct ScanResult {
    let mode: String // "entry" or "exit"
    let userName: String?
    let balance: Double?
    let stationCode: String?
    let gateCode: String?
    let usageAmount: Double? // 利用金額（将来的な機能）
}

#Preview {
    ContentView()
}
