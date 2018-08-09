//
//  SessionController.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 01/08/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SessionController: NSViewController {
    @IBOutlet weak var session_view: NSCollectionView!

    static let Title = "mvp — Sessions"

    override func viewDidLoad() {
        super.viewDidLoad()

        // Do any additional setup after loading the view.
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

    override var representedObject: Any? {
        didSet {
        // Update the view, if already loaded.
        }
    }


}

