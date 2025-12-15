//
//  GateSettingsView.swift
//  Felica_Gate_System
//
//  改札機の設定画面（駅・ゲート選択）
//

import SwiftUI

struct GateSettingsView: View {
    @AppStorage("station_code") private var stationCode = "STATION_1"
    @AppStorage("gate_code") private var gateCode = "STATION_1_IN"
    @AppStorage("gate_mode") private var gateMode = "transit"  // transit or retail
    @AppStorage("server_url") private var serverURL = "http://Shimayus-MacBook-Pro.local:8000"

    @State private var stations: [Station] = []
    @State private var gates: [Gate] = []
    @State private var isLoading = false
    @State private var errorMessage = ""

    // 選択された駅のゲートのみをフィルタリング
    private var filteredGates: [Gate] {
        // 選択された駅のIDを取得
        guard let selectedStation = stations.first(where: { $0.code == stationCode }) else {
            return gates
        }

        // 選択された駅のゲートのみを返す
        return gates.filter { $0.station_id == selectedStation.id }
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("サーバー設定")) {
                    TextField("サーバーURL", text: $serverURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        .font(.system(.body, design: .monospaced))

                    Button(action: loadStationsAndGates) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                            } else {
                                Image(systemName: "arrow.clockwise")
                                Text("駅・ゲート情報を取得")
                            }
                        }
                    }
                    .disabled(isLoading)
                }

                Section(header: Text("改札機モード")) {
                    Picker("モード", selection: $gateMode) {
                        Text("🚉 交通改札").tag("transit")
                        Text("🏪 物販レジ").tag("retail")
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }

                if gateMode == "transit" {
                    Section(header: Text("駅設定")) {
                        Picker("駅", selection: $stationCode) {
                            ForEach(stations, id: \.code) { station in
                                Text("\(station.name) (\(station.code))").tag(station.code)
                            }
                        }

                        TextField("駅コード（手動入力）", text: $stationCode)
                            .textInputAutocapitalization(.characters)
                    }

                    Section(header: Text("ゲート設定")) {
                        Picker("ゲート", selection: $gateCode) {
                            ForEach(filteredGates, id: \.code) { gate in
                                Text("\(gate.name) (\(gate.code))").tag(gate.code)
                            }
                        }

                        TextField("ゲートコード（手動入力）", text: $gateCode)
                            .textInputAutocapitalization(.characters)

                        if filteredGates.isEmpty && !stations.isEmpty {
                            Text("選択された駅にゲートがありません")
                                .foregroundColor(.orange)
                                .font(.caption)
                        }
                    }
                }

                Section(header: Text("現在の設定")) {
                    HStack {
                        Text("モード")
                        Spacer()
                        Text(gateMode == "transit" ? "交通改札" : "物販レジ")
                            .foregroundColor(.secondary)
                    }

                    if gateMode == "transit" {
                        HStack {
                            Text("駅")
                            Spacer()
                            Text(stationCode)
                                .foregroundColor(.secondary)
                        }

                        HStack {
                            Text("ゲート")
                            Spacer()
                            Text(gateCode)
                                .foregroundColor(.secondary)
                        }
                    }

                    HStack {
                        Text("サーバー")
                        Spacer()
                        Text(serverURL)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }

                if !errorMessage.isEmpty {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("改札機設定")
        }
        .onAppear {
            loadStationsAndGates()
        }
    }

    private func loadStationsAndGates() {
        isLoading = true
        errorMessage = ""

        guard let url = URL(string: serverURL) else {
            errorMessage = "無効なサーバーURL"
            isLoading = false
            return
        }

        let apiClient = APIClient(baseURL: url)

        // 駅情報を取得
        fetchStations(apiClient: apiClient)

        // ゲート情報を取得
        fetchGates(apiClient: apiClient)
    }

    private func fetchStations(apiClient: APIClient) {
        guard let url = URL(string: "\(serverURL)/stations") else { return }

        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                if let data = data {
                    do {
                        let decoded = try JSONDecoder().decode([Station].self, from: data)
                        stations = decoded
                    } catch {
                        errorMessage = "駅情報の解析に失敗: \(error.localizedDescription)"
                    }
                }
                isLoading = false
            }
        }.resume()
    }

    private func fetchGates(apiClient: APIClient) {
        guard let url = URL(string: "\(serverURL)/gates") else { return }

        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                if let data = data {
                    do {
                        let decoded = try JSONDecoder().decode([Gate].self, from: data)
                        gates = decoded
                    } catch {
                        errorMessage = "ゲート情報の解析に失敗: \(error.localizedDescription)"
                    }
                }
            }
        }.resume()
    }
}

struct Station: Codable {
    let id: Int
    let code: String
    let name: String
}

struct Gate: Codable {
    let id: Int
    let code: String
    let station_id: Int?
    let name: String
}

#Preview {
    GateSettingsView()
}
