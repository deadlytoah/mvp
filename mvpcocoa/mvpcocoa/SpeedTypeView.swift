//
//  SpeedTypeView.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 06/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

class SpeedTypeView: NSTextView {
    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        // Drawing code here.
    }

    override func keyDown(with theEvent: NSEvent) {
        nextResponder?.keyDown(with: theEvent)
    }

    override func changeFont(_ sender: Any?) {
        let fontManager = sender as! NSFontManager
        self.font = fontManager.convert(self.font!)
    }

    override func validateMenuItem(_ menuItem: NSMenuItem) -> Bool {
        if let action = menuItem.action {
            switch action.description {
            case "cut:", "paste:", "pasteAsPlainText:", "delete:",
                 "print:",
                 "underline:",
                 "outline:",
                 "showGuessPanel:",
                 "checkSpelling:",
                 "toggleContinuousSpellChecking:",
                 "toggleGrammarChecking:",
                 "toggleAutomaticSpellingCorrection:",
                 "replaceQuotesInSelection:",
                 "replaceDashesInSelection:",
                 "addLinksInSelection:",
                 "replaceTextInSelection:",
                 "orderFrontSubstitutionsPanel:",
                 "toggleSmartInsertDelete:",
                 "toggleAutomaticQuoteSubstitution:",
                 "toggleAutomaticDashSubstitution:",
                 "toggleAutomaticLinkDetection:",
                 "toggleAutomaticDataDetection:",
                 "toggleAutomaticTextReplacement:",
                 "uppercaseWord:",
                 "lowercaseWord:",
                 "capitalizeWord:",
                 "changeLayoutOrientation:",
                 "makeBaseWritingDirectionNatural:",
                 "makeBaseWritingDirectionLeftToRight:",
                 "makeBaseWritingDirectionRightToLeft:",
                 "makeTextWritingDirectionNatural:",
                 "makeTextWritingDirectionLeftToRight:",
                 "makeTextWritingDirectionRightToLeft:",
                 "alignLeft:",
                 "alignCenter:",
                 "alignJustified:",
                 "alignRight:",
                 "toggleRuler:",
                 "copyRuler:",
                 "pasteRuler:",
                 "copyFont:",
                 "pasteFont:",
                 "performFindPanelAction:",
                 "centerSelectionInVisibleArea:"
                :
                return false
            default:
                return true
            }
        } else {
            return true
        }
    }
}
