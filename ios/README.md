# iOS アプリ - 参考コードとドキュメント

このディレクトリは**参考資料**として保管されています。

## ⚠️ 重要

**実際のXcodeプロジェクトは `Felica_Gate_System/` ディレクトリにあります。**

このディレクトリ(`ios/`)のファイルは参考用であり、直接使用しません。
実装済みのコードは以下にあります：

```
Felica_Gate_System/
├── APIClient.swift      ← 実際に使用されるファイル
├── ContentView.swift    ← 実際に使用されるファイル
├── NFCReader.swift      ← 実際に使用されるファイル
├── QRScannerView.swift  ← 実際に使用されるファイル
└── Felica_Gate_SystemApp.swift
```

## このディレクトリの役割

- 📚 コード例とサンプル
- 📖 セットアップ手順のドキュメント（SETUP.md）
- 🔍 実装の参考資料

## セットアップ方法

詳細なセットアップ手順は [SETUP.md](SETUP.md) を参照してください。

## ファイル説明

### 参考コード
- `NFCReader.swift` - FeliCa IDm読み取りの実装例
- `QRScanner.swift` - QRコードスキャンの実装例
- `APIClient.swift` - サーバーAPI通信の実装例
- `ContentView-Sample.swift` - UIの実装例

### ドキュメント
- `SETUP.md` - 詳細なセットアップ手順
- `README.md` - このファイル
