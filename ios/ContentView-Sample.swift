import SwiftUI

struct ContentViewSample: View {
    @StateObject var nfc = NFCReader()
    @State var qrToken: String? = nil
    @State var resultText: String = ""

    let api = APIClient(baseURL: URL(string: "http://127.0.0.1:8000")!)

    var body: some View {
        VStack(spacing: 20) {
            Text("Felica Gate Scanner").font(.title)
            Button("Scan FeliCa") {
                nfc.startSession()
            }
            .onReceive(nfc.$lastIDm) { idm in
                guard let idm = idm else { return }
                sendScan(source: "felica", idm: idm, qr: nil)
            }

            Text("OR")

            NavigationLink(destination: QRScannerContainer(onFound: { token in
                self.qrToken = token
                sendScan(source: "qr", idm: nil, qr: token)
            })) {
                Text("Scan QR")
            }

            Text(resultText).padding()
        }
        .padding()
    }

    func sendScan(source: String, idm: String?, qr: String?) {
        let iso = ISO8601DateFormatter().string(from: Date())
        let req = ScanRequest(scan_source: source, card_idm: idm, qr_token: qr, station_code: "ST01", gate_code: "A1", timestamp: iso, device_id: "scanner-001")
        api.postScan(req: req) { res in
            switch res {
            case .success(let data):
                if let json = try? JSONSerialization.jsonObject(with: data, options: []) as? [String:Any] {
                    DispatchQueue.main.async {
                        if let mode = json["mode"] as? String {
                            self.resultText = "Result: \(mode)"
                        } else if let status = json["status"] as? String, status == "error" {
                            self.resultText = "Error: \(json["message"] ?? "")"
                        } else {
                            self.resultText = "Unknown response"
                        }
                    }
                }
            case .failure(let err):
                DispatchQueue.main.async {
                    self.resultText = "Network error: \(err.localizedDescription)"
                }
            }
        }
    }
}

struct QRScannerContainer: View {
    var onFound: (String) -> Void
    var body: some View {
        QRScannerView(onFound: { token in
            onFound(token)
        })
            .edgesIgnoringSafeArea(.all)
    }
}
