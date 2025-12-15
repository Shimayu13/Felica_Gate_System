//
//  UserRegistrationView.swift
//  Felica_Gate_System
//
//  ユーザー登録とQRコード発行画面
//

import SwiftUI

struct UserRegistrationView: View {
    @State private var name = ""
    @State private var email = ""
    @State private var initialBalance = "1000"
    @State private var registrationResult: RegistrationResult?
    @State private var errorMessage = ""
    @State private var isProcessing = false
    @State private var showQRCode = false

    let apiClient = APIClient(baseURL: URL(string: "http://192.168.1.66:8000")!)

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 25) {
                    // タイトル
                    VStack(spacing: 10) {
                        Image(systemName: "person.badge.plus")
                            .font(.system(size: 60))
                            .foregroundColor(.blue)

                        Text("新規ユーザー登録")
                            .font(.title)
                            .fontWeight(.bold)

                        Text("QRコードを発行します")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top, 30)

                    // 登録フォーム
                    VStack(spacing: 20) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("お名前 *")
                                .font(.headline)
                                .foregroundColor(.primary)

                            TextField("例: 山田太郎", text: $name)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .font(.body)
                        }

                        VStack(alignment: .leading, spacing: 8) {
                            Text("メールアドレス（任意）")
                                .font(.headline)
                                .foregroundColor(.primary)

                            TextField("例: yamada@example.com", text: $email)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                                .font(.body)
                        }

                        VStack(alignment: .leading, spacing: 8) {
                            Text("初期残高（円）")
                                .font(.headline)
                                .foregroundColor(.primary)

                            TextField("1000", text: $initialBalance)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.numberPad)
                                .font(.body)
                        }
                    }
                    .padding()
                    .background(Color.secondary.opacity(0.05))
                    .cornerRadius(12)

                    // 登録ボタン
                    Button(action: registerUser) {
                        HStack {
                            if isProcessing {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Image(systemName: "checkmark.circle.fill")
                                    .font(.title3)
                                Text("登録してQRコード発行")
                                    .fontWeight(.semibold)
                                    .font(.title3)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(name.isEmpty ? Color.gray : Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(name.isEmpty || isProcessing)

                    // エラーメッセージ
                    if !errorMessage.isEmpty {
                        VStack(spacing: 10) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 40))
                                .foregroundColor(.red)

                            Text(errorMessage)
                                .font(.body)
                                .multilineTextAlignment(.center)
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(12)
                        .foregroundColor(.red)
                    }

                    // 登録成功画面
                    if let result = registrationResult {
                        VStack(spacing: 20) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 70))
                                .foregroundColor(.green)

                            Text("登録完了！")
                                .font(.title)
                                .fontWeight(.bold)

                            Divider()
                                .padding(.horizontal)

                            VStack(alignment: .leading, spacing: 12) {
                                HStack {
                                    Image(systemName: "person.circle.fill")
                                        .foregroundColor(.blue)
                                    Text("名前:")
                                        .fontWeight(.medium)
                                    Spacer()
                                    Text(result.name)
                                }

                                HStack {
                                    Image(systemName: "yensign.circle.fill")
                                        .foregroundColor(.green)
                                    Text("残高:")
                                        .fontWeight(.medium)
                                    Spacer()
                                    Text("¥\(String(format: "%.0f", result.balance))")
                                        .font(.system(.body, design: .rounded))
                                        .fontWeight(.bold)
                                }

                                HStack {
                                    Image(systemName: "qrcode")
                                        .foregroundColor(.orange)
                                    Text("QRトークン:")
                                        .fontWeight(.medium)
                                    Spacer()
                                    Text(result.qrToken)
                                        .font(.system(.caption, design: .monospaced))
                                }
                            }
                            .padding()
                            .background(Color.secondary.opacity(0.1))
                            .cornerRadius(12)

                            Button(action: { showQRCode = true }) {
                                HStack {
                                    Image(systemName: "qrcode.viewfinder")
                                        .font(.title2)
                                    Text("QRコードを表示")
                                        .fontWeight(.semibold)
                                        .font(.title3)
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.green)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.green.opacity(0.05))
                        .cornerRadius(16)
                    }

                    Spacer()
                }
                .padding()
            }
            .navigationBarHidden(true)
        }
        .sheet(isPresented: $showQRCode) {
            if let result = registrationResult {
                QRCodeDisplayView(qrToken: result.qrToken, userName: result.name)
            }
        }
    }

    private func registerUser() {
        guard !name.isEmpty else { return }

        isProcessing = true
        errorMessage = ""
        registrationResult = nil

        let balance = Double(initialBalance) ?? 1000.0
        let emailParam = email.isEmpty ? nil : email

        var urlComponents = URLComponents(url: apiClient.baseURL.appendingPathComponent("register"), resolvingAgainstBaseURL: false)!
        var queryItems = [URLQueryItem(name: "name", value: name)]
        queryItems.append(URLQueryItem(name: "initial_balance", value: String(balance)))
        if let emailParam = emailParam {
            queryItems.append(URLQueryItem(name: "email", value: emailParam))
        }
        urlComponents.queryItems = queryItems

        var request = URLRequest(url: urlComponents.url!)
        request.httpMethod = "POST"

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                isProcessing = false

                if let error = error {
                    errorMessage = "ネットワークエラー:\n\(error.localizedDescription)"
                    return
                }

                guard let data = data else {
                    errorMessage = "データを受信できませんでした"
                    return
                }

                do {
                    let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

                    if let status = json?["status"] as? String, status == "ok",
                       let userName = json?["name"] as? String,
                       let userBalance = json?["balance"] as? Double,
                       let qrToken = json?["qr_token"] as? String {

                        registrationResult = RegistrationResult(
                            name: userName,
                            balance: userBalance,
                            qrToken: qrToken
                        )

                        // フォームをリセット
                        name = ""
                        email = ""
                        initialBalance = "1000"
                    } else {
                        errorMessage = "登録に失敗しました"
                    }
                } catch {
                    errorMessage = "応答の解析に失敗しました"
                }
            }
        }.resume()
    }
}

struct RegistrationResult {
    let name: String
    let balance: Double
    let qrToken: String
}

struct QRCodeDisplayView: View {
    let qrToken: String
    let userName: String
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                Text("\(userName)さんのQRコード")
                    .font(.title2)
                    .fontWeight(.bold)

                if let qrImage = generateQRCode(from: qrToken) {
                    Image(uiImage: qrImage)
                        .interpolation(.none)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 250, height: 250)
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                        .shadow(radius: 5)
                }

                Text(qrToken)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(.secondary)

                Text("このQRコードをゲートでスキャンしてください")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)

                Spacer()
            }
            .padding()
            .navigationBarItems(trailing: Button("閉じる") {
                presentationMode.wrappedValue.dismiss()
            })
        }
    }

    private func generateQRCode(from string: String) -> UIImage? {
        let data = Data(string.utf8)

        guard let qrFilter = CIFilter(name: "CIQRCodeGenerator") else { return nil }
        qrFilter.setValue(data, forKey: "inputMessage")
        qrFilter.setValue("H", forKey: "inputCorrectionLevel")

        guard let qrImage = qrFilter.outputImage else { return nil }

        let transform = CGAffineTransform(scaleX: 10, y: 10)
        let scaledQrImage = qrImage.transformed(by: transform)

        let context = CIContext()
        guard let cgImage = context.createCGImage(scaledQrImage, from: scaledQrImage.extent) else { return nil }

        return UIImage(cgImage: cgImage)
    }
}

#Preview {
    UserRegistrationView()
}
