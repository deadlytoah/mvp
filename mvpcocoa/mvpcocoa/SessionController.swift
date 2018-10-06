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
    @IBOutlet weak var openButton: NSButtonCell!
    @IBOutlet weak var deleteButton: NSButton!

    static let Title = "mvp — Sessions"

    var sessions = [Session]()

    override func viewDidLoad() {
        super.viewDidLoad()

        let itemNib = NSNib(nibNamed: NSNib.Name(rawValue: "SessionColViewItem"), bundle: nil)

        sessionView.register(itemNib, forItemWithIdentifier: NSUserInterfaceItemIdentifier(rawValue: "SessionColViewItem"))
        sessionView.delegate = self
        sessionView.dataSource = self

        self.view.window?.title = SessionController.Title

        do {
            self.sessions = try Session.listSessions()
        } catch {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Error getting the list of sessions (\(error) error)"
            alert.beginSheetModal(for: self.view.window!)
        }
    }

    func collectionView(_ collectionView: NSCollectionView, numberOfItemsInSection section: Int) -> Int {
        return self.sessions.count
    }

    func collectionView(_ collectionView: NSCollectionView, itemForRepresentedObjectAt indexPath: IndexPath) -> NSCollectionViewItem {
        let item = sessionView.makeItem(withIdentifier: NSUserInterfaceItemIdentifier(rawValue: "SessionColViewItem"), for: indexPath)
        item.textField!.stringValue = self.sessions[indexPath[1]].name
        return item
    }

    func collectionView(_ collectionView: NSCollectionView, didSelectItemsAt indexPaths: Set<IndexPath>) {
        assert(indexPaths.count == 1)
        let item = collectionView.item(at: indexPaths.first!)!
        let box = item.view as! NSBox
        box.isTransparent = false
        item.textField!.textColor = NSColor.alternateSelectedControlTextColor

        openButton.isEnabled = true
        deleteButton.isEnabled = true
    }

    func collectionView(_ collectionView: NSCollectionView, didDeselectItemsAt indexPaths: Set<IndexPath>) {
        assert(indexPaths.count == 1)
        let item = collectionView.item(at: indexPaths.first!)!
        let box = item.view as! NSBox
        box.isTransparent = true
        item.textField!.textColor = NSColor.controlTextColor

        openButton.isEnabled = false
        deleteButton.isEnabled = false
    }

    @IBAction func performOpen(_ sender: Any) {
        let indexPaths = sessionView!.selectionIndexPaths
        assert(indexPaths.count == 1)
        let session = self.sessions[indexPaths.first!.item]
        let speedTypeController = self.presenting as! SpeedTypeController
        speedTypeController.beginSession(session: session)

        self.dismiss(self)
    }

    func sessionSelected(session: Session) {
        let speedTypeController = self.presenting as! SpeedTypeController
        speedTypeController.beginSession(session: session)
        self.dismiss(self)
    }

    override var representedObject: Any? {
        didSet {
        // Update the view, if already loaded.
        }
    }


}

