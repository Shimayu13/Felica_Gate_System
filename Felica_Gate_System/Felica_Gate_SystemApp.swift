//
//  Felica_Gate_SystemApp.swift
//  Felica_Gate_System
//
//  Created by Yuki Shimazu on 2025/12/11.
//

import SwiftUI

@main
struct Felica_Gate_SystemApp: App {
    init() {
        // 古い駅コードをクリアして新しいシステムに移行
        migrateStationCodes()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }

    private func migrateStationCodes() {
        let oldStationCodes = [
            "ST01", "ST02", "ST03",  // 旧テストデータ
            "JK01", "JK02", "JK03", "JK04", "JK05", "JK06", "JK07", "JK08", "JK09", "JK10",
            "JK11", "JK12", "JK13", "JK14", "JK15", "JK16", "JK17", "JK18", "JK19", "JK20",
            "JK21", "JK22", "JK23", "JK24", "JK25", "JK26",  // 京浜東北線
            "JO01", "JO02", "JO03", "JO04", "JO05", "JO06", "JO07", "JO08", "JO09",  // 横須賀線
            "JN01", "JN02", "JN03", "JN04", "JN05", "JN06", "JN07", "JN08", "JN09", "JN10",
            "JN11", "JN12", "JN13", "JN14", "JN15", "JN16", "JN17", "JN18", "JN19", "JN20"  // 南武線
        ]

        let currentStationCode = UserDefaults.standard.string(forKey: "station_code") ?? ""
        let currentGateCode = UserDefaults.standard.string(forKey: "gate_code") ?? ""

        // 古い駅コードが保存されている場合は削除
        if oldStationCodes.contains(currentStationCode) ||
           currentStationCode.hasPrefix("JK") ||
           currentStationCode.hasPrefix("JO") ||
           currentStationCode.hasPrefix("JN") ||
           currentStationCode.hasPrefix("ST") {
            print("🔄 古い駅コードを検出: \(currentStationCode)")
            print("🔄 新しいシステムに移行します...")

            // 古い設定を削除（デフォルト値が使用される）
            UserDefaults.standard.removeObject(forKey: "station_code")
            UserDefaults.standard.removeObject(forKey: "gate_code")
            UserDefaults.standard.synchronize()

            print("✅ 移行完了: STATION_1 / STATION_1_IN")
        }

        // ゲートコードも古い形式の場合は削除
        if currentGateCode.contains("JK") ||
           currentGateCode.contains("JO") ||
           currentGateCode.contains("JN") ||
           currentGateCode == "A1" ||
           currentGateCode == "A2" {
            UserDefaults.standard.removeObject(forKey: "gate_code")
            UserDefaults.standard.synchronize()
        }
    }
}
