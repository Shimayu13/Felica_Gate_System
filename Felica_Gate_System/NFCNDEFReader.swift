//
//  NFCNDEFReader.swift
//  Felica_Gate_System
//
//  一般的なNFCタグ（NDEF）読み取り用
//  FeliCa申請不要で使用可能
//

import Foundation
import CoreNFC

class NFCNDEFReader: NSObject, NFCNDEFReaderSessionDelegate {
    private var session: NFCNDEFReaderSession?
    private var completion: ((Result<String, Error>) -> Void)?

    enum NFCError: LocalizedError {
        case invalidTag
        case readFailed
        case noIdentifier
        case sessionCancelled

        var errorDescription: String? {
            switch self {
            case .invalidTag:
                return "無効なタグです"
            case .readFailed:
                return "読み取りに失敗しました"
            case .noIdentifier:
                return "タグIDが取得できませんでした"
            case .sessionCancelled:
                return "読み取りがキャンセルされました"
            }
        }
    }

    func startReading(completion: @escaping (Result<String, Error>) -> Void) {
        self.completion = completion

        guard NFCNDEFReaderSession.readingAvailable else {
            completion(.failure(NFCError.readFailed))
            return
        }

        session = NFCNDEFReaderSession(delegate: self, queue: nil, invalidateAfterFirstRead: true)
        session?.alertMessage = "NFCタグをiPhoneの背面にかざしてください"
        session?.begin()
    }

    // MARK: - NFCNDEFReaderSessionDelegate

    func readerSessionDidBecomeActive(_ session: NFCNDEFReaderSession) {
        print("📱 NFC NDEF session started")
    }

    func readerSession(_ session: NFCNDEFReaderSession, didInvalidateWithError error: Error) {
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

    func readerSession(_ session: NFCNDEFReaderSession, didDetectNDEFs messages: [NFCNDEFMessage]) {
        print("📇 NDEF messages detected: \(messages.count)")

        // NDEFメッセージからペイロードを取得
        var tagData = ""
        for message in messages {
            for record in message.records {
                if let payload = String(data: record.payload, encoding: .utf8) {
                    tagData += payload
                }
            }
        }

        if !tagData.isEmpty {
            session.alertMessage = "読み取り成功！"
            completion?(.success(tagData))
            completion = nil
        }
    }

    func readerSession(_ session: NFCNDEFReaderSession, didDetect tags: [NFCNDEFTag]) {
        print("🏷️  NDEF tags detected, count: \(tags.count)")

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

            // タグの種類を確認してIDを取得
            tag.queryNDEFStatus { status, capacity, error in
                if let error = error {
                    session.invalidate(errorMessage: "タグ情報の取得に失敗しました")
                    self.completion?(.failure(error))
                    self.completion = nil
                    return
                }

                // タグのIDを取得（タグの種類によって異なる）
                var tagId: String?

                // MiFareタグの場合
                if let mifareTag = tag as? NFCMiFareTag {
                    let identifier = mifareTag.identifier
                    tagId = identifier.map { String(format: "%02X", $0) }.joined()
                    print("📇 MiFare Tag Identifier: \(tagId ?? "N/A")")
                }
                // ISO15693タグの場合
                else if let iso15693Tag = tag as? NFCISO15693Tag {
                    let identifier = iso15693Tag.identifier
                    tagId = identifier.map { String(format: "%02X", $0) }.joined()
                    print("📇 ISO15693 Tag Identifier: \(tagId ?? "N/A")")
                }
                // ISO7816タグの場合
                else if let iso7816Tag = tag as? NFCISO7816Tag {
                    let identifier = iso7816Tag.identifier
                    tagId = identifier.map { String(format: "%02X", $0) }.joined()
                    print("📇 ISO7816 Tag Identifier: \(tagId ?? "N/A")")
                }

                if let tagId = tagId {
                    session.alertMessage = "読み取り成功！"
                    session.invalidate()

                    self.completion?(.success(tagId))
                    self.completion = nil
                } else {
                    session.invalidate(errorMessage: "タグIDが取得できませんでした")
                    self.completion?(.failure(NFCError.noIdentifier))
                    self.completion = nil
                }
            }
        }
    }
}
