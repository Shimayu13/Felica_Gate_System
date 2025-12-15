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
    init(baseURL: URL) { self.baseURL = baseURL }

    func postScan(req: ScanRequest, completion: @escaping (Result<Data, Error>) -> Void) {
        guard let url = URL(string: "/scan", relativeTo: baseURL) else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        do {
            request.httpBody = try JSONEncoder().encode(req)
        } catch {
            completion(.failure(error))
            return
        }
        URLSession.shared.dataTask(with: request) { data, resp, err in
            if let e = err { completion(.failure(e)); return }
            completion(.success(data ?? Data()))
        }.resume()
    }
}
