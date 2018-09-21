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

    var state: SpeedtypeState? = nil

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
            let state = speedtype_new()

            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    _ = String(cString: &verse.key.0)
                    let text = String(cString: &verse.text.0)

                    let textStorage = self.speedTypeView.textStorage!
                    textStorage.append(NSAttributedString(string: "\(text)\n"))

                    let retval = speedtype_process_line(state!, text)
                    if retval != 0 {
                        let alert = NSAlert()
                        alert.alertStyle = .critical
                        alert.messageText = "Error processing line with code \(retval)."
                        alert.beginSheetModal(for: self.view.window!)
                    }
                }
            })

            self.state = SpeedtypeState(raw: state!.pointee)
            self.caret_position = 0
            self.render()

            speedtype_delete(state)
        } else {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Retrieving Bible verses failed with code \(retval)."
            alert.beginSheetModal(for: self.view.window!)
        }
    }

    private func render() {
        let caret = self.caret_position

        let textStorage = self.speedTypeView.textStorage!
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = CGFloat(lineSpacing)
        var attributes = [NSAttributedStringKey.font: self.font!,
                          NSAttributedStringKey.foregroundColor: guideColour,
                          NSAttributedStringKey.paragraphStyle: paragraphStyle]

        for ch in self.state!.buffer.filter({ ch in !ch.rendered }) {
            var string = String(ch.character)
            if ch.typed != nil {
                if ch.correct {
                    attributes[NSAttributedStringKey.foregroundColor] = self.correctColour
                } else {
                    attributes[NSAttributedStringKey.foregroundColor] = self.incorrectColour

                    if (ch.word == nil || !self.state!.words[ch.word!].visible) && !ch.newline {
                        string = String(ch.typed!)
                    }
                }
            } else {
                attributes[NSAttributedStringKey.foregroundColor] = self.guideColour
            }
            textStorage.replaceCharacters(in: NSRange(location: ch.id, length: 1), with: NSAttributedString(string: string, attributes: attributes))
            ch.rendered = true
        }

        self.caret_position = caret
    }

    // Override the NSView keydown func to read keycode of pressed key
    override func keyDown(with theEvent: NSEvent) {
        self.interpretKeyEvents([theEvent])
        self.speedTypeView.scrollRangeToVisible(NSRange(location: self.caret_position, length: 1))
    }

    override func insertText(_ string: Any) {
        let s: String = string as! String
        let buffer = self.state!.buffer

        for ch in s {
            let caret = self.caret_position
            buffer[caret].typed = ch
            buffer[caret].correct = buffer[caret].character == ch
            buffer[caret].rendered = false
            self.caret_position = caret + 1
        }
        self.render()
    }

    override func deleteBackward(_ sender: Any?) {
        let caret = self.caret_position
        if caret > 0 {
            let ch = self.state!.buffer[caret - 1]
            ch.correct = false
            ch.typed = nil
            ch.rendered = false

            self.caret_position = caret - 1
            self.render()
        }
    }

    override func insertNewline(_ sender: Any?) {
        insertText(" ")
    }
}
