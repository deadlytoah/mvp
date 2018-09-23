//
//  SessionController.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 01/08/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SessionController: NSViewController, NSCollectionViewDelegate, NSCollectionViewDataSource {
    @IBOutlet weak var sessionView: NSCollectionView!

    static let Title = "mvp — Sessions"

    let BufferSize = 20
    var sessions: Array<Session> = []

    override func viewDidLoad() {
        super.viewDidLoad()

        let itemNib = NSNib(nibNamed: NSNib.Name(rawValue: "SessionColViewItem"), bundle: nil)

        sessionView.register(itemNib, forItemWithIdentifier: NSUserInterfaceItemIdentifier(rawValue: "SessionColViewItem"))
        sessionView.delegate = self
        sessionView.dataSource = self
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        self.view.window?.title = SessionController.Title

        var len = BufferSize
        self.sessions = Array<Session>(repeating: Session.init(), count: len)

        self.sessions.withUnsafeMutableBufferPointer { ptr in
            let retcode = session_list_sessions(ptr.baseAddress!, UnsafeMutablePointer(&len))
            if retcode != 0 {
                let alert = NSAlert()
                alert.alertStyle = .critical
                alert.messageText = String(cString: session_get_message(retcode))
                alert.beginSheetModal(for: self.view.window!)
            }
        }

        self.sessions.removeLast(BufferSize - len)
    }

    func collectionView(_ collectionView: NSCollectionView, numberOfItemsInSection section: Int) -> Int {
        return self.sessions.count
    }

    func collectionView(_ collectionView: NSCollectionView, itemForRepresentedObjectAt indexPath: IndexPath) -> NSCollectionViewItem {
        let item = sessionView.makeItem(withIdentifier: NSUserInterfaceItemIdentifier(rawValue: "SessionColViewItem"), for: indexPath)
        withUnsafePointer(to: &self.sessions[indexPath[1]].name.0, { ptr in
            let name = String(cString: ptr)
            item.textField?.stringValue = name
        })
        return item
    }

    override var representedObject: Any? {
        didSet {
        // Update the view, if already loaded.
        }
    }


}

