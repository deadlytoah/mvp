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

        var len = 4096
        var buf = Array<Int8>(repeating: 0, count: len)

        buf.withUnsafeMutableBufferPointer { ptr in
            let retcode = session_list_sessions(ptr.baseAddress!, UnsafeMutablePointer(&len))
            if retcode != 0 {
                let alert = NSAlert()
                alert.alertStyle = .critical
                alert.messageText = String(cString: session_get_message(retcode))
                alert.beginSheetModal(for: self.view.window!)
            }
        }
    }

    func collectionView(_ collectionView: NSCollectionView, numberOfItemsInSection section: Int) -> Int {
        // TODO implement this
        return 5
    }

    func collectionView(_ collectionView: NSCollectionView, itemForRepresentedObjectAt indexPath: IndexPath) -> NSCollectionViewItem {
        let item = sessionView.makeItem(withIdentifier: NSUserInterfaceItemIdentifier(rawValue: "SessionColViewItem"), for: indexPath)
        item.textField?.stringValue = "Session \(indexPath[1] + 1)"
        return item
    }

    override var representedObject: Any? {
        didSet {
        // Update the view, if already loaded.
        }
    }


}

