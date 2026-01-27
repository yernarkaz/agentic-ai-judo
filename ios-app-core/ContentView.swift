import SwiftUI

struct ContentView: View {
    @StateObject private var networkManager = NetworkManager()
    @State private var showPicker = false
    @State private var selectedVideoURL: URL?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                if let result = networkManager.analysisResult {
                    AnalysisView(result: result)
                } else if networkManager.isUploading {
                    VStack {
                        ProgressView()
                            .scaleEffect(1.5)
                        Text("Analyzing Video... This may take a while.")
                            .padding(.top)
                    }
                } else {
                    VStack(spacing: 20) {
                        Image(systemName: "figure.martial.arts")
                            .font(.system(size: 100))
                            .foregroundColor(.blue)
                        
                        Text("Judo Analysis Coach")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .multilineTextAlignment(.center)
                        
                        Text("Upload a video to get AI-driven technique analysis.")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.bottom, 50)
                    
                    Button(action: {
                        showPicker = true
                    }) {
                        HStack {
                            Image(systemName: "video.badge.plus")
                            Text("Select Video")
                        }
                        .font(.headline)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal, 40)
                }

                if let error = networkManager.errorMessage {
                    Text(error)
                        .foregroundColor(.red)
                        .padding()
                        .multilineTextAlignment(.center)
                }
            }
            .navigationTitle(networkManager.analysisResult == nil ? "Home" : "Results")
            .sheet(isPresented: $showPicker) {
                VideoPicker(videoURL: $selectedVideoURL)
            }
            .onChange(of: selectedVideoURL) { newUrl in
                if let url = newUrl {
                    networkManager.uploadVideo(at: url)
                }
            }
        }
    }
}
