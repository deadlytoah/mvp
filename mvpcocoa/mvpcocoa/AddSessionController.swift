//
//  AddSessionController.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 04/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class AddSessionController: NSViewController {

    @IBOutlet weak var translation: NSTextField!
    @IBOutlet weak var name: NSTextField!
    @IBOutlet weak var book: NSTextField!
    @IBOutlet weak var chapter: NSTextField!
    @IBOutlet weak var level: NSTextField!
    @IBOutlet weak var strategy: NSTextField!

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    @IBAction func performOk(_ sender: Any) {
        let start = Location(translation: translation.stringValue, book: book.stringValue, chapter: UInt16(chapter.integerValue), sentence: 0, verse: 1)
        let end = Location(translation: translation.stringValue, book: book.stringValue, chapter: UInt16(chapter.integerValue), sentence: 1, verse: 2)
        let session = Session(name: name.stringValue, range: (start, end), level: Level(rawValue: UInt8(level.integerValue))!, strategy: Strategy(raw: UInt8(strategy.integerValue)))

        do {
            try session.create()

            let sessionController = self.presenting as! SessionController
            sessionController.sessionSelected(session: session)

            self.dismiss(self)
        } catch {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Failed to create a new session (\(error) error)"
            alert.beginSheetModal(for: self.view.window!)
        }
   }

    @IBAction func performCancel(_ sender: Any) {
        self.dismiss(self)
    }
}
