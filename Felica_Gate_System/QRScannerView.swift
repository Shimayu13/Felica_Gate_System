//
//  QRScannerView.swift
//  Felica_Gate_System
//

import SwiftUI
import AVFoundation

struct QRScannerView: UIViewControllerRepresentable {
    var onFound: (String) -> Void

    func makeUIViewController(context: Context) -> QRScannerViewController {
        let controller = QRScannerViewController()
        controller.delegate = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: QRScannerViewController, context: Context) {
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(onFound: onFound)
    }

    class Coordinator: NSObject, QRScannerDelegate {
        var onFound: (String) -> Void

        init(onFound: @escaping (String) -> Void) {
            self.onFound = onFound
        }

        func didFindCode(_ code: String) {
            onFound(code)
        }
    }
}

protocol QRScannerDelegate: AnyObject {
    func didFindCode(_ code: String)
}

class QRScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    weak var delegate: QRScannerDelegate?

    private var captureSession: AVCaptureSession?
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var lastScannedCode: String?
    private var lastScanTime: Date?
    private var isScanningEnabled = true

    override func viewDidLoad() {
        super.viewDidLoad()
        setupCamera()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)

        if let session = captureSession, !session.isRunning {
            DispatchQueue.global(qos: .userInitiated).async {
                session.startRunning()
            }
        }
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)

        if let session = captureSession, session.isRunning {
            session.stopRunning()
        }
    }

    private func setupCamera() {
        let session = AVCaptureSession()
        captureSession = session

        // フロントカメラ（前面カメラ）を使用
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            showAlert(message: "フロントカメラが見つかりません")
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: device)
            session.addInput(input)
        } catch {
            showAlert(message: "カメラの初期化に失敗しました")
            return
        }

        let output = AVCaptureMetadataOutput()
        session.addOutput(output)

        output.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
        output.metadataObjectTypes = [.qr]

        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        self.previewLayer = previewLayer

        DispatchQueue.global(qos: .userInitiated).async {
            session.startRunning()
        }
    }

    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        // スキャンが無効化されている場合はスキップ
        guard isScanningEnabled else { return }

        if let metadataObject = metadataObjects.first,
           let readableObject = metadataObject as? AVMetadataMachineReadableCodeObject,
           let stringValue = readableObject.stringValue {

            // 同じコードを連続でスキャンしないように制御
            // 前回と同じコードで、2秒以内の場合はスキップ
            if let lastCode = lastScannedCode,
               let lastTime = lastScanTime,
               lastCode == stringValue,
               Date().timeIntervalSince(lastTime) < 2.0 {
                return
            }

            // スキャン情報を記録
            lastScannedCode = stringValue
            lastScanTime = Date()

            // 一時的にスキャンを無効化（処理中の重複防止）
            isScanningEnabled = false

            // バイブレーション
            AudioServicesPlaySystemSound(SystemSoundID(kSystemSoundID_Vibrate))

            // デリゲートに通知
            delegate?.didFindCode(stringValue)

            // 1.5秒後にスキャンを再開
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
                self?.isScanningEnabled = true
            }
        }
    }

    private func showAlert(message: String) {
        let alert = UIAlertController(title: "エラー", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.layer.bounds
    }
}
