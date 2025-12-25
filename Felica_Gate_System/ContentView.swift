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
    @State private var scanMode: ScanMode = .qr  // QR, FeliCa, または 顔認証
    @State private var showFaceCamera = false

    @AppStorage("station_code") private var stationCode = "STATION_1"
    @AppStorage("gate_code") private var gateCode = "GATE_1"
    @AppStorage("server_url") private var serverURL = "http://Shimayus-MacBook-Pro.local:8000"

    private var apiClient: APIClient {
        APIClient(baseURL: URL(string: serverURL)!)
    }

    // FeliCa読み取り（CoreNFC直接実装）
    private let feliCaReader = NFCFeliCaReader()

    enum ScanMode {
        case qr
        case felica  // 「FeliCa」という名前ですが、一般NFCタグも読めます
        case face
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
                                // モード切替ボタン
                                HStack(spacing: 15) {
                                    Button(action: { scanMode = .qr }) {
                                        VStack(spacing: 8) {
                                            Image(systemName: "qrcode.viewfinder")
                                                .font(.system(size: 35))
                                            Text("QRコード")
                                                .font(.caption)
                                        }
                                        .frame(width: 90, height: 75)
                                        .background(scanMode == .qr ? Color.blue.opacity(0.2) : Color.gray.opacity(0.1))
                                        .foregroundColor(scanMode == .qr ? .blue : .gray)
                                        .cornerRadius(12)
                                    }

                                    Button(action: { scanMode = .felica }) {
                                        VStack(spacing: 8) {
                                            Image(systemName: "creditcard.fill")
                                                .font(.system(size: 35))
                                            Text("FeliCa")
                                                .font(.caption)
                                        }
                                        .frame(width: 90, height: 75)
                                        .background(scanMode == .felica ? Color.orange.opacity(0.2) : Color.gray.opacity(0.1))
                                        .foregroundColor(scanMode == .felica ? .orange : .gray)
                                        .cornerRadius(12)
                                    }

                                    Button(action: { scanMode = .face }) {
                                        VStack(spacing: 8) {
                                            Image(systemName: "faceid")
                                                .font(.system(size: 35))
                                            Text("顔認証")
                                                .font(.caption)
                                        }
                                        .frame(width: 90, height: 75)
                                        .background(scanMode == .face ? Color.green.opacity(0.2) : Color.gray.opacity(0.1))
                                        .foregroundColor(scanMode == .face ? .green : .gray)
                                        .cornerRadius(12)
                                    }
                                }
                                .padding(.bottom, 10)

                                Image(systemName: scanMode == .qr ? "qrcode.viewfinder" : (scanMode == .felica ? "creditcard.fill" : "faceid"))
                                    .font(.system(size: 80))
                                    .foregroundColor(.gray)

                                Text(scanMode == .qr ? "QRコードをスキャンしてください" : (scanMode == .felica ? "FeliCaカードをタッチしてください" : "顔認証で入退場できます"))
                                    .font(.title3)
                                    .foregroundColor(.secondary)

                                if scanMode == .face {
                                    Button(action: { showFaceCamera = true }) {
                                        HStack {
                                            Image(systemName: "camera.fill")
                                            Text("顔認証を開始")
                                        }
                                        .font(.headline)
                                        .foregroundColor(.white)
                                        .padding()
                                        .background(Color.green)
                                        .cornerRadius(12)
                                    }
                                    .padding(.top, 10)
                                } else if scanMode == .felica {
                                    Button(action: { startFeliCaScan() }) {
                                        HStack {
                                            Image(systemName: "wave.3.right")
                                            Text("FeliCa読み取り開始")
                                        }
                                        .font(.headline)
                                        .foregroundColor(.white)
                                        .padding()
                                        .background(Color.orange)
                                        .cornerRadius(12)
                                    }
                                    .padding(.top, 10)
                                }
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

                // 下部：QRスキャナー または FeliCa/顔認証待機画面（1/3の高さ）
                ZStack {
                    if scanMode == .qr {
                        QRScannerView { token in
                            sendScan(qrToken: token)
                        }
                        .frame(height: geometry.size.height * 1 / 3)
                    } else if scanMode == .felica {
                        // FeliCaモードの場合
                        Color(UIColor.systemBackground)
                            .frame(height: geometry.size.height * 1 / 3)
                            .overlay(
                                VStack(spacing: 15) {
                                    Image(systemName: "wave.3.right.circle.fill")
                                        .font(.system(size: 60))
                                        .foregroundColor(.orange.opacity(0.5))

                                    Text("上のボタンからFeliCa読み取りを開始")
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }
                            )
                    } else {
                        // 顔認証モードの場合
                        Color(UIColor.systemBackground)
                            .frame(height: geometry.size.height * 1 / 3)
                            .overlay(
                                VStack(spacing: 15) {
                                    Image(systemName: "faceid")
                                        .font(.system(size: 60))
                                        .foregroundColor(.green.opacity(0.5))

                                    Text("上のボタンから顔認証を開始")
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }
                            )
                    }

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
        .fullScreenCover(isPresented: $showFaceCamera) {
            FaceCameraView(
                onCapture: { image in
                    showFaceCamera = false
                    sendFaceVerify(faceImage: image)
                },
                onCancel: {
                    showFaceCamera = false
                }
            )
        }
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
            face_image_base64: nil,
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

    private func sendFaceVerify(faceImage: UIImage) {
        isProcessing = true
        resultMessage = ""
        scanResult = nil
        cancelScheduledClear()

        apiClient.postScanWithFace(faceImage: faceImage, stationCode: stationCode, gateCode: gateCode) { result in
            DispatchQueue.main.async {
                isProcessing = false

                switch result {
                case .success(let data):
                    handleScanResponse(data, qrToken: nil)
                case .failure(let error):
                    resultMessage = "ネットワークエラー:\n\(error.localizedDescription)"
                    scanResult = nil
                    GateSound.playError()
                    scheduleClearDisplay()
                }
            }
        }
    }

    private func startFeliCaScan() {
        isProcessing = true
        resultMessage = ""
        scanResult = nil
        cancelScheduledClear()

        // CoreNFC直接実装でFeliCa読み取り
        feliCaReader.startReading { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let idm):
                    print("📇 FeliCa読み取り成功")
                    print("   IDm: \(idm)")

                    // IDmをサーバーに送信
                    self.sendFeliCaScan(cardIdm: idm)

                case .failure(let error):
                    self.isProcessing = false
                    self.resultMessage = "FeliCa読み取りエラー:\n\(error.localizedDescription)"
                    self.scanResult = nil
                    GateSound.playError()
                    self.scheduleClearDisplay()
                }
            }
        }
    }

    private func sendFeliCaScan(cardIdm: String) {
        let request = ScanRequest(
            scan_source: "felica",
            card_idm: cardIdm,
            qr_token: nil,
            face_image_base64: nil,
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
                    handleScanResponse(data, qrToken: nil)
                case .failure(let error):
                    resultMessage = "ネットワークエラー:\n\(error.localizedDescription)"
                    scanResult = nil
                    GateSound.playError()
                    scheduleClearDisplay()
                }
            }
        }
    }

    private func handleScanResponse(_ data: Data, qrToken: String?) {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

            if let mode = json?["mode"] as? String {
                let usageAmount = json?["usage_amount"] as? Double
                let balanceAfterScan = json?["balance"] as? Double
                let userId = json?["user_id"] as? Int

                GateSound.playSuccess()

                // QRトークンがある場合は従来のフローでユーザー情報を取得
                // 顔認証の場合（qrToken == nil）は直接ユーザー情報を取得
                if let qrToken = qrToken {
                    // QRスキャンの場合
                    fetchUserInfo(
                        qrToken: qrToken,
                        mode: mode,
                        usageAmount: usageAmount,
                        balanceOverride: balanceAfterScan,
                        userIdHint: userId
                    )
                } else if let userId = userId {
                    // 顔認証の場合 - user_idから直接取得
                    fetchUserDetails(
                        userId: userId,
                        mode: mode,
                        usageAmount: usageAmount,
                        balanceOverride: balanceAfterScan
                    )
                } else {
                    resultMessage = "ユーザー情報の取得に失敗しました"
                    scanResult = nil
                    scheduleClearDisplay()
                }
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
