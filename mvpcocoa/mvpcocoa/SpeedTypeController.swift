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
        let translation = "esv"
        let retval = translation.withCString({translationPtr in
            withUnsafeMutablePointer(to: &verseView, {viewPtr in
                verse_find_all(translationPtr, viewPtr)
            })
        })

        if retval == 0 {
            let textStorage = self.speedTypeView.textStorage
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    _ = withUnsafePointer(to: &verse.key.0, { ptr in
                        return String(cString: ptr)
                    })
                    let text = withUnsafePointer(to: &verse.text.0, { ptr in
                        return String(cString: ptr)
                    })
                    textStorage?.append(NSAttributedString(string: "\(text)\n"))
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
