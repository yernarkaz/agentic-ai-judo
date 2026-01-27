import Combine
import Foundation
import SwiftUI

class NetworkManager: ObservableObject {
    @Published var analysisResult: AnalysisResult?
    @Published var isUploading = false
    @Published var errorMessage: String?
    
    // Use 127.0.0.1 for Simulator
    private let baseURL = "http://127.0.0.1:8000"
    
    func uploadVideo(at fileURL: URL) {
        self.isUploading = true
        self.errorMessage = nil
        self.analysisResult = nil
        
        let url = URL(string: "\(baseURL)/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        // Load video data
        guard let videoData = try? Data(contentsOf: fileURL) else {
            self.errorMessage = "Could not load video data"
            self.isUploading = false
            return
        }
        
        let filename = fileURL.lastPathComponent
        
        // Build Body
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)
        body.append(videoData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        URLSession.shared.uploadTask(with: request, from: body) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    self?.errorMessage = error.localizedDescription
                    self?.isUploading = false
                    return
                }
                
                guard let data = data else {
                    self?.errorMessage = "No data received"
                    self?.isUploading = false
                    return
                }
                
                do {
                    let response = try JSONDecoder().decode(VideoResponse.self, from: data)
                    print("Upload success: \(response.video_id)")
                    // Start polling
                    self?.pollForAnalysis(videoId: response.video_id)
                } catch {
                    self?.errorMessage = "Failed to decode response: \(error.localizedDescription)"
                    self?.isUploading = false
                }
            }
        }.resume()
    }
    
    func pollForAnalysis(videoId: String) {
        let url = URL(string: "\(baseURL)/analyze/\(videoId)")!
        
        // Poll every 5 seconds
        Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] timer in
            URLSession.shared.dataTask(with: url) { data, response, error in
                DispatchQueue.main.async {
                    if let error = error {
                        print("Polling error: \(error)")
                        return
                    }
                    
                    guard let data = data else { return }
                    
                    do {
                        let result = try JSONDecoder().decode(AnalysisResult.self, from: data)
                        if result.status == "completed" {
                            self?.analysisResult = result
                            self?.isUploading = false
                            timer.invalidate()
                        } else if result.status == "error" {
                            self?.errorMessage = result.error ?? "Unknown error"
                            self?.isUploading = false
                            timer.invalidate()
                        }
                        // If pending, continue polling
                    } catch {
                         print("Decoding error: \(error)")
                    }
                }
            }.resume()
        }
    }
}
