import Foundation

struct VideoResponse: Codable {
    let video_id: String
    let filename: String
    let message: String
}

struct AnalysisResult: Codable {
    let video_id: String
    let status: String
    let analysis: String?
    let error: String?
}
