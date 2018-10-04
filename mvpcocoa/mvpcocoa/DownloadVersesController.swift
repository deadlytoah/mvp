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

    var translation: String? = nil
    var location: Location? = nil

    override func viewDidLoad() {
        super.viewDidLoad()

        // disable resize
        preferredContentSize = self.view.bounds.size

        spinningWheel.startAnimation(self)

        DispatchQueue.global(qos: .background).async {
            do {
                let verses = try Verse.fetchVersesByBookAndChapter(translation: self.translation!, source: VerseSourceBlueLetterBible, book: self.location!.book, chapter: self.location!.chapter)

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
