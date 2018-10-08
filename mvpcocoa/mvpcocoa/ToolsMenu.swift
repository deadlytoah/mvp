//
//  ToolsMenu.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 08/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa
import Foundation

extension SpeedTypeController {
    @IBAction
    func createCacheDatabase(_ sender: Any) {
        let msg = NSAlert()
        msg.addButton(withTitle: "OK")      // 1st button
        msg.addButton(withTitle: "Cancel")  // 2nd button
        msg.messageText = "Create a New Cache Database:"
        msg.informativeText = "Enter the name of the Bible translation to create a cache for:"

        let txt = NSTextField(frame: NSRect(x: 0, y: 0, width: 200, height: 24))
        msg.accessoryView = txt
        let response: NSApplication.ModalResponse = msg.runModal()

        if (response == NSApplication.ModalResponse.alertFirstButtonReturn) {
            let ret = cache_create(txt.stringValue)
            if ret != 0 {
                let alert = NSAlert()
                alert.alertStyle = .critical
                alert.messageText = "Failed to create the new cache with \(ret)."
                alert.beginSheetModal(for: self.view.window!)
            }
        }
    }
}
