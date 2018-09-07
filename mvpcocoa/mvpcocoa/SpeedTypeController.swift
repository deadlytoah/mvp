//
//  SpeedTypeController.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 06/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SpeedTypeController: NSViewController {
    @IBOutlet weak var titleLabel: NSTextField!
    @IBOutlet weak var difficultySlider: NSSlider!
    @IBOutlet weak var speedTypeView: SpeedTypeView!

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()

        var verseView = VerseView()
        let retval = verse_find_by_book_and_chapter("esv", &verseView, "Phl", 1)

        if retval == 0 {
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    _ = String(cString: &verse.key.0)
                    let text = String(cString: &verse.text.0)
                    self.speedTypeView.lines.append(text)
                }
            })
        } else {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Retrieving Bible verses failed with code \(retval)."
            alert.beginSheetModal(for: self.view.window!)
        }
    }
}
