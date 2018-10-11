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

    let defaultFont = NSFont(name: "Courier New", size: 18)
    let guideColour = NSColor.gray
    let correctColour = NSColor.black
    let incorrectColour = NSColor.red
    let underscoreColour = NSColor.lightGray
    let lineSpacing = 10.0

    var session: Session? = nil

    var state: SpeedTypeState? = nil {
        didSet {
            self.difficultyLevel = Int(session!.level.toByte())
        }
    }

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
                    state.applyLevel(UInt8(difficultyLevel))
                    self.session!.level = Level(raw: UInt8(difficultyLevel))
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

        self.speedTypeView.font = self.defaultFont
        DispatchQueue.main.async {
            self.openSession(self)
        }
    }

    @IBAction
    func openSession(_ sender: Any) {
        self.performSegue(withIdentifier: NSStoryboardSegue.Identifier("sessionSegue"), sender: self)
    }

    override func prepare(for segue: NSStoryboardSegue, sender: Any?) {
        if segue.identifier == NSStoryboardSegue.Identifier("downloadVersesSegue") {
            let downloadVersesController = segue.destinationController as! DownloadVersesController
            downloadVersesController.representedObject = session
        }
    }

    func beginSession(session: Session) {
        self.session = session

        do {
            let verseList = try Verse.findVersesByBookAndChapter(translation: session.range.0.translation, book: session.range.0.book, chapter: session.range.0.chapter)
            if !verseList.isEmpty {
                let layout = createTextLayout(verseList: verseList)
                fillTextView(lines: layout)
                self.state = initialiseState(lines: layout)
                self.render()
                self.speedTypeView?.moveToBeginningOfDocument(self)
            } else {
                self.state = nil
                DispatchQueue.main.async {
                    self.performSegue(withIdentifier: NSStoryboardSegue.Identifier("downloadVersesSegue"), sender: self)
                }
            }
        } catch {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Retrieving Bible verses failed with \(error)."
            alert.beginSheetModal(for: self.view.window!)
        }
    }

    func versesDownloaded(verses: [Verse]) {
        do {
            try Verse.insertVersesForBookAndChapter(translation: session!.range.0.translation, book: session!.range.0.book, chapter: session!.range.0.chapter, verses: verses)
        } catch {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Inserting Bible verses failed with \(error)."
            alert.beginSheetModal(for: self.view.window!)
        }

        let layout = createTextLayout(verseList:verses)
        fillTextView(lines: layout)
        self.state = initialiseState(lines: layout)

        self.render()
        self.speedTypeView?.moveToBeginningOfDocument(self)
    }

    fileprivate func createTextLayout(verseList: [Verse]) -> [String] {
        var layout: [String] = []
        Sentence.sentencesFromVerses(verses: verseList.map { verse in
            verse.text
        }).forEach { sentence in
            graphLayout(text: sentence.text).forEach { line in
                layout.append(line)
            }
        }
        return layout
    }

    fileprivate func fillTextView(lines: [String]) {
        self.speedTypeView!.string = lines.joined(separator: "\n") + "\n"
    }

    fileprivate func initialiseState(lines: [String]) -> SpeedTypeState {
        let state = SpeedTypeState()
        lines.forEach { line in
            do {
                try state.processLine(line)
            } catch {
                let alert = NSAlert()
                alert.alertStyle = .critical
                alert.messageText = "Error processing line with code \(error)."
                alert.beginSheetModal(for: self.view.window!)
                return
            }
        }
        return state
    }

    @IBAction
    func sliderMoved(_ sender: Any?) {
        self.difficultyLevel = self.difficultySlider.integerValue
    }

    private func render() {
        self.titleLabel.stringValue = "\(self.session!.name) – \(self.session!.level) difficulty"

        let textStorage = self.speedTypeView.textStorage!
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = CGFloat(lineSpacing)
        var attributes = [NSAttributedStringKey.font: self.speedTypeView.font!,
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

            if caret < buffer.count {
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
