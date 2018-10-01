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
    let underscoreColour = NSColor.lightGray
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

    // Source of truth:  Changing this property propagates to
    // the slider and the hidden words in the text.
    var difficultyLevel: Int = 0 {
        didSet {
            if oldValue != difficultyLevel {
                self.difficultySlider.integerValue = difficultyLevel
                if let state = self.state {
                    let caret = caret_position
                    speedtype_apply_level(state.raw, UInt8(difficultyLevel))
                    self.render()
                    if caret != caret_position {
                        caret_position = caret
                    }
                }
            }
        }
    }

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()

        var verseView = VerseView()
        let retval = verse_find_by_book_and_chapter("esv", &verseView, "Phil", 2)

        if retval == 0 {
            if verseView.count == 0 {
                let retval = verse_fetch_by_book_and_chapter("esv", &verseView, VerseSourceBlueLetterBible, "Phil", 2)
                if retval != 0 {
                    // igonoring for now, because there is no other option.
                    // But we will let user manually enter the verses in
                    // the future.
                    Swift.print("error fetching")
                }
            }

            let state = speedtype_new()

            var verseList: [String] = []
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    _ = String(cString: &verse.key.0)
                    verseList.append(String(cString: &verse.text.0))
                }
            })

            verseList.forEach({ verse in
                for line in graphLayout(text: verse) {
                    let textStorage = self.speedTypeView.textStorage!
                    textStorage.append(NSAttributedString(string: "\(line)\n"))

                    let retval = speedtype_process_line(state!, line)
                    if retval != 0 {
                        let alert = NSAlert()
                        alert.alertStyle = .critical
                        alert.messageText = "Error processing line with code \(retval)."
                        alert.beginSheetModal(for: self.view.window!)
                    }
                }
            })

            self.state = SpeedtypeState(raw: state!)
            self.render()
            self.speedTypeView?.moveToBeginningOfDocument(self)
        } else {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Retrieving Bible verses failed with code \(retval)."
            alert.beginSheetModal(for: self.view.window!)
        }
    }

    @IBAction
    func sliderMoved(_ sender: Any?) {
        self.difficultyLevel = self.difficultySlider.integerValue
    }

    private func render() {
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
                if ch.visible {
                    attributes[NSAttributedStringKey.foregroundColor] = self.guideColour
                } else if ch.whitespace {
                    string = " "
                    attributes[NSAttributedStringKey.foregroundColor] = self.speedTypeView.backgroundColor
                } else {
                    string = "_"
                    attributes[NSAttributedStringKey.foregroundColor] = self.underscoreColour
                }
            }
            textStorage.replaceCharacters(in: NSRange(location: ch.id, length: 1), with: NSAttributedString(string: string, attributes: attributes))
            ch.rendered = true
        }
    }

    // Override the NSView keydown func to read keycode of pressed key
    override func keyDown(with theEvent: NSEvent) {
        self.interpretKeyEvents([theEvent])
    }

    override func insertText(_ string: Any) {
        let s: String = string as! String
        let buffer = self.state!.buffer

        for ch in s {
            let caret = self.caret_position
            buffer[caret].typed = ch
            buffer[caret].correct = buffer[caret].character == ch

            if let word = buffer[caret].word {
                let word = self.state!.words[word]
                word.touched = true

                // we are at the last letter, which means we are done
                // with this word.
                if caret == word.chars.last! {
                    word.behind = true
                }
            }

            buffer[caret].rendered = false
            self.speedTypeView?.moveForward(self)
        }
        self.render()
    }

    override func deleteBackward(_ sender: Any?) {
        let caret = self.caret_position
        if caret > 0 {
            let ch = self.state!.buffer[caret - 1]
            ch.correct = false
            ch.typed = nil
            if let word = ch.word {
                let word = self.state!.words[word]
                word.behind = false
            }

            ch.rendered = false
            self.render()
            self.speedTypeView?.moveBackward(self)
        }
    }

    override func insertNewline(_ sender: Any?) {
        insertText(" ")
    }
}
