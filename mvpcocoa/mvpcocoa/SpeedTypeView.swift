//
//  SpeedTypeView.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 06/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SpeedTypeView: NSTextView {
    var lines: [String] = []

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        // Drawing code here.
        NSString(string: lines[0]).draw(at: NSPoint(x: 0, y: 200), withAttributes: nil)
    }
}
