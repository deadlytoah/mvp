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

    // Allow view to receive keypress (remove the purr sound)
    override var acceptsFirstResponder : Bool {
        return true
    }

    // Override the NSView keydown func to read keycode of pressed key
    override func keyDown(with theEvent: NSEvent) {
        if theEvent.characters != nil {
            for ch in theEvent.characters! {
                let caret = self.caret_position
                self.textStorage?.mutableString.replaceCharacters(in: NSRange(location: caret, length: 1), with: String(ch))
                self.textStorage?.addAttribute(NSAttributedStringKey.foregroundColor, value: NSColor.black, range: NSRange(location: caret, length: 1))
            }
        }
    }
}
