//
//  DownloadVersesController.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 04/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class DownloadVersesController: NSViewController {

    @IBOutlet weak var spinningWheel: NSProgressIndicator!

    override func viewDidLoad() {
        super.viewDidLoad()

        // disable resize
        preferredContentSize = self.view.bounds.size

        spinningWheel.startAnimation(self)

        DispatchQueue.global(qos: .background).async {
            do {
                let session = self.representedObject as! Session
                let verses = try Verse.fetchVersesByBookAndChapter(translation: session.range.0.translation, source: VerseSourceBlueLetterBible, book: session.range.0.book, chapter: session.range.0.chapter)

                DispatchQueue.main.async {
                    let speedTypeController = self.presenting! as! SpeedTypeController
                    speedTypeController.versesDownloaded(verses: verses)
                    self.dismiss(self)
                }
            } catch {
                DispatchQueue.main.async {
                    let alert = NSAlert()
                    alert.alertStyle = .critical
                    alert.messageText = "Failed to download Bible verses (\(error) error)"
                    alert.beginSheetModal(for: self.view.window!) { response in
                        self.enterVersesManually(self)
                    }
                }
            }
        }
    }

    @IBAction func enterVersesManually(_ sender: Any) {
        let alert = NSAlert()
        alert.alertStyle = .informational
        alert.messageText = "Enter verses functionality is not implemented yet"
        alert.beginSheetModal(for: self.view.window!) { response in
            self.dismiss(sender)
        }
    }
}
