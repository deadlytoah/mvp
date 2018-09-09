//
//  SpeedTypeView.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 06/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SpeedTypeView: NSTextView {
    var caret_position: Int {
        get {
            let range = self.selectedRanges[0].rangeValue
            return range.location + range.length
        }
        set {
            self.selectedRange = NSRange(location: newValue, length: 0)
        }
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        // Drawing code here.
    }
}
