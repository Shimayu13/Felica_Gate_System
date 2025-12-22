//
//  APIClient.swift
//  Felica_Gate_System
//

import Foundation
import UIKit

struct ScanRequest: Codable {
    let scan_source: String
    let card_idm: String?
    let qr_token: String?
    let station_code: String
    let gate_code: String
    let timestamp: String
    let device_id: String
}

class APIClient {
    let baseURL: URL

    init(baseURL: URL) {
        self.baseURL = baseURL
    }

    func postScan(request: ScanRequest, completion: @escaping (Result<Data, Error>) -> Void) {
        let url = baseURL.appendingPathComponent("scan")

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            urlRequest.httpBody = try JSONEncoder().encode(request)
        } catch {
            completion(.failure(error))
            return
        }

        let task = URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            completion(.success(data))
        }

        task.resume()
    }

    func getUser(userId: Int, completion: @escaping (Result<Data, Error>) -> Void) {
        let url = baseURL.appendingPathComponent("users/\(userId)")

        let task = URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            completion(.success(data))
        }

        task.resume()
    }

    func getCards(completion: @escaping (Result<Data, Error>) -> Void) {
        let url = baseURL.appendingPathComponent("cards")

        let task = URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            completion(.success(data))
        }

        task.resume()
    }

    func postPurchase(request: PurchaseRequest, completion: @escaping (Result<Data, Error>) -> Void) {
        let url = baseURL.appendingPathComponent("retail/purchase")

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            urlRequest.httpBody = try JSONEncoder().encode(request)
        } catch {
            completion(.failure(error))
            return
        }

        let task = URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            completion(.success(data))
        }

        task.resume()
    }

    func postFaceVerify(faceImage: UIImage, completion: @escaping (Result<Data, Error>) -> Void) {
        let url = baseURL.appendingPathComponent("face/verify/upload")

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.timeoutInterval = 60.0  // 60秒のタイムアウト（顔検出に時間がかかるため）

        // マルチパートフォームデータを構築
        let boundary = UUID().uuidString
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // 画像をJPEGデータに変換（圧縮率を下げてサイズを小さく）
        guard let imageData = faceImage.jpegData(compressionQuality: 0.6) else {
            completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to convert image to JPEG"])))
            return
        }

        print("📤 顔認証: imageSize=\(imageData.count) bytes")

        var body = Data()

        // ファイルフィールドを追加
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"face.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        urlRequest.httpBody = body

        // URLSession の設定をカスタマイズ
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60.0
        config.timeoutIntervalForResource = 120.0
        let session = URLSession(configuration: config)

        let task = session.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                print("📥 顔認証エラー: \(error.localizedDescription)")
                if let urlError = error as? URLError {
                    print("📥 URLError code: \(urlError.code.rawValue)")
                }
                completion(.failure(error))
                return
            }

            if let httpResponse = response as? HTTPURLResponse {
                print("📥 顔認証レスポンス Status: \(httpResponse.statusCode)")
            }

            guard let data = data else {
                print("📥 データなし")
                completion(.failure(NSError(domain: "APIClient", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }

            if let responseString = String(data: data, encoding: .utf8) {
                print("📥 顔認証レスポンス: \(responseString)")
            }

            completion(.success(data))
        }

        task.resume()
    }
}

struct PurchaseRequest: Codable {
    let scan_source: String
    let qr_token: String
    let amount: Double
    let store_code: String
    let device_id: String
    let timestamp: String
}
