//
//  APIClient.swift
//  Felica_Gate_System
//

import Foundation

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
}

struct PurchaseRequest: Codable {
    let scan_source: String
    let qr_token: String
    let amount: Double
    let store_code: String
    let device_id: String
    let timestamp: String
}
