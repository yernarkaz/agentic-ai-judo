import SwiftUI
import PhotosUI
import UniformTypeIdentifiers

struct VideoPicker: UIViewControllerRepresentable {
    @Binding var videoURL: URL?

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .videos
        config.selectionLimit = 1
        
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: VideoPicker

        init(_ parent: VideoPicker) {
            self.parent = parent
        }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)

            guard let provider = results.first?.itemProvider,
                  provider.hasItemConformingToTypeIdentifier(UTType.movie.identifier) else { return }

            provider.loadFileRepresentation(forTypeIdentifier: UTType.movie.identifier) { url, error in
                if let url = url {
                    // PHPicker gives a temp URL that we must copy immediately
                    let fileName = "\(UUID().uuidString).mov"
                    let newURL = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
                    try? FileManager.default.copyItem(at: url, to: newURL)
                    
                    DispatchQueue.main.async {
                        self.parent.videoURL = newURL
                    }
                }
            }
        }
    }
}
