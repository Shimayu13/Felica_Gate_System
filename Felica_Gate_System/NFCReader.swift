//
//  NFCReader.swift
//  Felica_Gate_System
//

import Foundation
import CoreNFC
import Combine

class NFCReader: NSObject, ObservableObject, NFCTagReaderSessionDelegate {
    @Published var lastIDm: String?
    @Published var errorMessage: String?

    private var session: NFCTagReaderSession?

    func startSession() {
        guard NFCTagReaderSession.readingAvailable else {
            errorMessage = "このデバイスはNFCに対応していません"
            return
        }

        session = NFCTagReaderSession(pollingOption: .iso18092, delegate: self)
        session?.alertMessage = "FeliCaカードをiPhoneに近づけてください"
        session?.begin()
    }

    func tagReaderSessionDidBecomeActive(_ session: NFCTagReaderSession) {
        // セッションがアクティブになった
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didInvalidateWithError error: Error) {
        if let nfcError = error as? NFCReaderError {
            if nfcError.code != .readerSessionInvalidationErrorUserCanceled {
                DispatchQueue.main.async {
                    self.errorMessage = "NFCエラー: \(error.localizedDescription)"
                }
            }
        }
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didDetect tags: [NFCTag]) {
        guard let tag = tags.first else {
            session.invalidate(errorMessage: "タグが見つかりませんでした")
            return
        }

        session.connect(to: tag) { error in
            if let error = error {
                session.invalidate(errorMessage: "接続エラー: \(error.localizedDescription)")
                return
            }

            // FeliCaタグの処理
            if case let .feliCa(feliCaTag) = tag {
                let idm = feliCaTag.currentIDm.map { String(format: "%02X", $0) }.joined()

                DispatchQueue.main.async {
                    self.lastIDm = idm
                }

                session.alertMessage = "読み取り成功！"
                session.invalidate()
            } else {
                session.invalidate(errorMessage: "FeliCaカードではありません")
            }
        }
    }
}
