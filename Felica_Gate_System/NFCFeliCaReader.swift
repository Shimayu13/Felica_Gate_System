//
//  NFCFeliCaReader.swift
//  Felica_Gate_System
//
//  FeliCa読み取り（交通系IC対応）
//  参考: https://zenn.dev/naoya_maeda/articles/1b77acad397620
//

import Foundation
import CoreNFC

class NFCFeliCaReader: NSObject, NFCTagReaderSessionDelegate {
    private var session: NFCTagReaderSession?
    private var completion: ((Result<String, Error>) -> Void)?

    enum NFCError: LocalizedError {
        case invalidTag
        case readFailed
        case notFeliCa
        case sessionCancelled
        case unsupportedDevice

        var errorDescription: String? {
            switch self {
            case .invalidTag:
                return "無効なタグです"
            case .readFailed:
                return "読み取りに失敗しました"
            case .notFeliCa:
                return "FeliCaカードではありません"
            case .sessionCancelled:
                return "読み取りがキャンセルされました"
            case .unsupportedDevice:
                return "このデバイスはNFC読み取りに対応していません"
            }
        }
    }

    func startReading(completion: @escaping (Result<String, Error>) -> Void) {
        self.completion = completion

        guard NFCTagReaderSession.readingAvailable else {
            print("❌ NFC読み取りが利用できません（実機でのみ動作します）")
            completion(.failure(NFCError.unsupportedDevice))
            return
        }

        // ISO18092 (FeliCa) ポーリングオプションでセッション開始
        session = NFCTagReaderSession(pollingOption: .iso18092, delegate: self, queue: nil)
        session?.alertMessage = "FeliCaカード（Suica・PASMO等）をiPhoneの背面にかざしてください"
        session?.begin()

        print("📱 NFC FeliCaセッション開始")
    }

    // MARK: - NFCTagReaderSessionDelegate

    func tagReaderSessionDidBecomeActive(_ session: NFCTagReaderSession) {
        print("📱 NFC session started")
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didInvalidateWithError error: Error) {
        print("❌ NFC session invalidated: \(error.localizedDescription)")

        if let completion = self.completion {
            let nfcError = error as NSError
            if nfcError.code == 200 { // User cancelled
                completion(.failure(NFCError.sessionCancelled))
            } else {
                completion(.failure(error))
            }
            self.completion = nil
        }
    }

    func tagReaderSession(_ session: NFCTagReaderSession, didDetect tags: [NFCTag]) {
        print("🏷️  Tag detected, count: \(tags.count)")

        guard let tag = tags.first else {
            session.invalidate(errorMessage: "タグが検出されませんでした")
            completion?(.failure(NFCError.invalidTag))
            completion = nil
            return
        }

        session.connect(to: tag) { error in
            if let error = error {
                session.invalidate(errorMessage: "タグへの接続に失敗しました")
                self.completion?(.failure(error))
                self.completion = nil
                return
            }

            // FeliCaタグの処理
            switch tag {
            case .feliCa(let feliCaTag):
                self.handleFeliCaTag(feliCaTag, session: session)
            default:
                session.invalidate(errorMessage: "FeliCaカードではありません")
                self.completion?(.failure(NFCError.notFeliCa))
                self.completion = nil
            }
        }
    }

    private func handleFeliCaTag(_ tag: NFCFeliCaTag, session: NFCTagReaderSession) {
        print("💳 FeliCa tag detected")

        // IDmを取得（FeliCaカードの固有ID）
        let idm = tag.currentIDm
        let idmHex = idm.map { String(format: "%02X", $0) }.joined()
        print("📇 IDm: \(idmHex)")

        // システムコード取得
        let systemCode = tag.currentSystemCode
        let systemCodeHex = systemCode.map { String(format: "%02X", $0) }.joined()
        print("🔢 System Code: \(systemCodeHex)")

        // 交通系ICカードの判定
        let isTransitCard = ["0003", "00F0", "00F1", "00F2"].contains(systemCodeHex)
        if isTransitCard {
            print("🚃 交通系ICカード検出（Suica/PASMO等）")
        }

        // 残高読み取りを試みる（オプショナル）
        // Note: 交通系ICカードの詳細情報読み取りにはApple承認が必要な場合があります
        readBalance(from: tag, session: session, idmHex: idmHex)
    }

    private func readBalance(from tag: NFCFeliCaTag, session: NFCTagReaderSession, idmHex: String) {
        // サービスコード: 0x090F (残高情報)
        let serviceCode: Data = Data([0x09, 0x0F])
        let serviceCodeList = [Data(serviceCode.reversed())]

        // ブロックリスト (1ブロック読み取り)
        let blockList = [Data([0x80, 0x00])]

        tag.readWithoutEncryption(serviceCodeList: serviceCodeList, blockList: blockList) { status1, status2, blocks, error in
            if let error = error {
                print("⚠️ 残高読み取りエラー: \(error.localizedDescription)")
                print("   → カード認証が必要、またはApple承認が必要な可能性があります")

                // エラーでも成功として扱い、IDmを返す
                session.alertMessage = "カード読み取り成功！"
                session.invalidate()
                self.completion?(.success(idmHex))
                self.completion = nil
                return
            }

            // 残高情報取得成功
            if let blockData = blocks.first, blockData.count >= 12 {
                // バイト10-11が残高（リトルエンディアン）
                let balanceBytes = blockData[10...11]
                let balance = UInt16(balanceBytes[0]) | (UInt16(balanceBytes[1]) << 8)
                print("💰 残高: ¥\(balance)")
            }

            session.alertMessage = "読み取り成功！"
            session.invalidate()
            self.completion?(.success(idmHex))
            self.completion = nil
        }
    }
}
