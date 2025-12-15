import Foundation
import CoreNFC
import Combine

@available(iOS 13.0, *)
class NFCReader: NSObject, ObservableObject {
    @Published var lastIDm: String? = nil
    private var session: NFCTagReaderSession?

    func startSession() {
        guard NFCTagReaderSession.readingAvailable else {
            print("NFC not available")
            return
        }
        session = NFCTagReaderSession(pollingOption: [.iso18092], delegate: self)
        session?.alertMessage = "Hold your iPhone near the FeliCa card"
        session?.begin()
    }
}

@available(iOS 13.0, *)
extension NFCReader: NFCTagReaderSessionDelegate {
    func tagReaderSessionDidBecomeActive(_ session: NFCTagReaderSession) {
        // session active
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didInvalidateWithError error: Error) {
        print("NFC session invalidated: \(error)")
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didDetect tags: [NFCTag]) {
        guard let tag = tags.first else { return }
        session.connect(to: tag) { (error) in
            if let err = error {
                session.invalidate(errorMessage: "Connection error: \(err.localizedDescription)")
                return
            }

            switch tag {
            case .feliCa(let feliCaTag):
                // FeliCa: IDm is `currentIDm` or `idm` accessible via `manufacturerParameter` depending on API
                let idmData = feliCaTag.currentIDm
                let idm = idmData.map { String(format: "%02X", $0) }.joined()
                DispatchQueue.main.async {
                    self.lastIDm = idm
                    session.alertMessage = "IDm: \(idm)"
                    session.invalidate()
                }
            default:
                session.invalidate(errorMessage: "Unsupported tag")
            }
        }
    }
}
