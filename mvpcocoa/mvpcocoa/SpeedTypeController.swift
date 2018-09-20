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

    let font = NSFont(name: "Courier New", size: 18)
    let guideColour = NSColor.gray
    let correctColour = NSColor.black
    let incorrectColour = NSColor.red
    let lineSpacing = 10.0

    var model = ""
    var correct: [String.Index] = []
    var incorrect: [String.Index] = []

    var caret_position: Int {
        get {
            let range = self.speedTypeView.selectedRanges[0].rangeValue
            return range.location + range.length
        }
        set {
            self.speedTypeView.selectedRange = NSRange(location: newValue, length: 0)
        }
    }

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()

        var verseView = VerseView()
        let retval = verse_find_by_book_and_chapter("esv", &verseView, "Phl", 1)

        if retval == 0 {
            model = ""
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    _ = String(cString: &verse.key.0)
                    let text = String(cString: &verse.text.0)
                    model.append(text + "\n")
                }
            })

            self.caret_position = 0

            self.render()
        } else {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Retrieving Bible verses failed with code \(retval)."
            alert.beginSheetModal(for: self.view.window!)
        }
    }

    private func render() {
        let caret = self.caret_position

        let textStorage = self.speedTypeView.textStorage
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = CGFloat(lineSpacing)
        let attributes = [NSAttributedStringKey.font: self.font!,
                          NSAttributedStringKey.foregroundColor: guideColour,
                          NSAttributedStringKey.paragraphStyle: paragraphStyle]

        textStorage?.setAttributedString(NSAttributedString(string: self.model, attributes: attributes))

        for correct in self.correct {
            self.speedTypeView.textStorage?.addAttribute(NSAttributedStringKey.foregroundColor, value: self.correctColour, range: NSRange(location: correct.encodedOffset, length: 1))
        }

        for incorrect in self.incorrect {
            self.speedTypeView.textStorage?.addAttribute(NSAttributedStringKey.foregroundColor, value: self.incorrectColour, range: NSRange(location: incorrect.encodedOffset, length: 1))
        }

        self.caret_position = caret
    }

    // Override the NSView keydown func to read keycode of pressed key
    override func keyDown(with theEvent: NSEvent) {
        self.interpretKeyEvents([theEvent])
    }

    override func insertText(_ string: Any) {
        let s: String = string as! String
        for ch in s {
            let caret = String.Index(encodedOffset: self.caret_position)
            if ch == self.model[caret] {
                self.correct.append(caret)
                self.incorrect = Array(self.incorrect.drop(while: { i in
                    i == caret
                }))
            } else {
                self.incorrect.append(caret)
                self.correct = Array(self.correct.drop(while: { i in
                    i == caret
                }))
            }
            self.caret_position = caret.encodedOffset + 1
        }
        self.render()
    }

    override func deleteBackward(_ sender: Any?) {
        let caret = self.caret_position
        if caret > 0 {
            self.speedTypeView.textStorage?.addAttribute(NSAttributedStringKey.foregroundColor, value: NSColor.gray, range: NSRange(location: caret - 1, length: 1))
            self.caret_position = caret - 1
        }
    }

    override func insertNewline(_ sender: Any?) {
        let caret = self.caret_position
        model.insert("\n", at: String.Index(encodedOffset: caret))
        self.render()
        self.caret_position = caret + 1
    }
}
