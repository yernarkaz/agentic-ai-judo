//
//  JudoAnalysisApp.swift
//  JudoAnalysis
//
//  Created by Yernar Smagulov on 27.01.2026.
//

import SwiftUI
import CoreData

@main
struct JudoAnalysisApp: App {
    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
