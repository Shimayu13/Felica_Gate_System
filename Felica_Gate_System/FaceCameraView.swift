import SwiftUI
import AVFoundation
import Combine

struct FaceCameraView: View {
    @StateObject private var camera = FaceCameraModel()
    let onCapture: (UIImage) -> Void
    let onCancel: () -> Void

    var body: some View {
        ZStack {
            // カメラプレビュー
            CameraPreview(camera: camera)
                .ignoresSafeArea()

            // オーバーレイ
            VStack {
                // 上部：ガイダンス
                VStack(spacing: 8) {
                    Text("顔認証")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.white)

                    Text("顔を枠内に収めてください")
                        .font(.subheadline)
                        .foregroundColor(.white)
                }
                .padding()
                .background(Color.black.opacity(0.5))
                .cornerRadius(12)
                .padding(.top, 50)

                Spacer()

                // 中央：顔検出ガイド枠
                RoundedRectangle(cornerRadius: 150)
                    .stroke(Color.green.opacity(0.8), lineWidth: 3)
                    .frame(width: 280, height: 350)
                    .overlay(
                        // ドット装飾
                        ZStack {
                            Circle()
                                .fill(Color.green)
                                .frame(width: 8, height: 8)
                                .offset(x: -140, y: -175)
                            Circle()
                                .fill(Color.green)
                                .frame(width: 8, height: 8)
                                .offset(x: 140, y: -175)
                            Circle()
                                .fill(Color.green)
                                .frame(width: 8, height: 8)
                                .offset(x: -140, y: 175)
                            Circle()
                                .fill(Color.green)
                                .frame(width: 8, height: 8)
                                .offset(x: 140, y: 175)
                        }
                    )

                Spacer()

                // 下部：コントロールボタン
                HStack(spacing: 40) {
                    // キャンセルボタン
                    Button(action: onCancel) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.white)
                            .background(
                                Circle()
                                    .fill(Color.red.opacity(0.3))
                                    .frame(width: 70, height: 70)
                            )
                    }

                    // 撮影ボタン
                    Button(action: {
                        camera.capturePhoto { image in
                            if let image = image {
                                onCapture(image)
                            }
                        }
                    }) {
                        ZStack {
                            Circle()
                                .fill(Color.white)
                                .frame(width: 70, height: 70)
                            Circle()
                                .stroke(Color.white, lineWidth: 4)
                                .frame(width: 80, height: 80)
                        }
                    }
                }
                .padding(.bottom, 50)
            }
        }
        .onAppear {
            camera.checkPermissions()
        }
        .alert("カメラアクセス", isPresented: $camera.showPermissionAlert) {
            Button("設定を開く") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("キャンセル", role: .cancel) {
                onCancel()
            }
        } message: {
            Text("顔認証を使用するにはカメラへのアクセスを許可してください")
        }
    }
}

// カメラプレビュー
struct CameraPreview: UIViewRepresentable {
    @ObservedObject var camera: FaceCameraModel

    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: .zero)
        view.backgroundColor = .black

        camera.preview = AVCaptureVideoPreviewLayer(session: camera.session)
        camera.preview.frame = view.bounds
        camera.preview.videoGravity = .resizeAspectFill
        view.layer.addSublayer(camera.preview)

        camera.session.startRunning()

        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        DispatchQueue.main.async {
            camera.preview.frame = uiView.bounds
        }
    }
}

// カメラモデル
class FaceCameraModel: NSObject, ObservableObject, AVCapturePhotoCaptureDelegate {
    @Published var session = AVCaptureSession()
    @Published var showPermissionAlert = false

    var preview = AVCaptureVideoPreviewLayer()
    var output = AVCapturePhotoOutput()
    private var captureCompletion: ((UIImage?) -> Void)?

    func checkPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            setupCamera()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    if granted {
                        self.setupCamera()
                    } else {
                        self.showPermissionAlert = true
                    }
                }
            }
        case .denied, .restricted:
            DispatchQueue.main.async {
                self.showPermissionAlert = true
            }
        @unknown default:
            break
        }
    }

    func setupCamera() {
        do {
            session.beginConfiguration()

            // フロントカメラを使用
            guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
                print("フロントカメラが見つかりません")
                return
            }

            let input = try AVCaptureDeviceInput(device: device)

            if session.canAddInput(input) {
                session.addInput(input)
            }

            if session.canAddOutput(output) {
                session.addOutput(output)
            }

            session.commitConfiguration()
        } catch {
            print("カメラ設定エラー: \(error)")
        }
    }

    func capturePhoto(completion: @escaping (UIImage?) -> Void) {
        self.captureCompletion = completion

        let settings = AVCapturePhotoSettings()
        output.capturePhoto(with: settings, delegate: self)
    }

    // AVCapturePhotoCaptureDelegate
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        if let error = error {
            print("写真キャプチャエラー: \(error)")
            captureCompletion?(nil)
            return
        }

        guard let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            captureCompletion?(nil)
            return
        }

        // フロントカメラの場合、画像を左右反転
        // 注意: 顔認証の精度を上げるため、反転を無効化してテスト
        // let flippedImage = UIImage(cgImage: image.cgImage!, scale: image.scale, orientation: .leftMirrored)

        // 反転なしでテスト
        captureCompletion?(image)
    }
}

#Preview {
    FaceCameraView(
        onCapture: { _ in },
        onCancel: { }
    )
}
