import SwiftUI

struct AnalysisView: View {
    let result: AnalysisResult
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Analysis Complete")
                    .font(.title)
                    .foregroundColor(.green)
                
                if let analysis = result.analysis {
                    Text(analysis)
                        .font(.body)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                } else {
                    Text("No analysis text provided.")
                }
                
                if let error = result.error {
                    Text("Error: \(error)")
                        .foregroundColor(.red)
                }
            }
            .padding()
        }
    }
}
