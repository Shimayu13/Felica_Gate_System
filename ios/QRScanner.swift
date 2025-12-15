import Foundation
import SwiftUI
import AVFoundation

class QRScannerCoordinator: NSObject, AVCaptureMetadataOutputObjectsDelegate {
    var parent: QRScannerView
    init(parent: QRScannerView) { self.parent = parent }

    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        if let metadata = metadataObjects.first as? AVMetadataMachineReadableCodeObject, let string = metadata.stringValue {
            DispatchQueue.main.async {
                self.parent.onFound(string)
            }
        }
    }
}

struct QRScannerView: UIViewRepresentable {
    var onFound: (String) -> Void

    func makeCoordinator() -> QRScannerCoordinator { QRScannerCoordinator(parent: self) }

    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        let session = AVCaptureSession()
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            return view
        }
        guard let input = try? AVCaptureDeviceInput(device: device) else { return view }
        session.addInput(input)

        let output = AVCaptureMetadataOutput()
        session.addOutput(output)
        output.setMetadataObjectsDelegate(context.coordinator, queue: DispatchQueue.main)
        output.metadataObjectTypes = [.qr]

        let preview = AVCaptureVideoPreviewLayer(session: session)
        preview.videoGravity = .resizeAspectFill
        preview.frame = view.layer.bounds
        preview.connection?.videoOrientation = .portrait
        view.layer.addSublayer(preview)

        session.startRunning()
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {}
}
