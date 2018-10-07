//
//  Verse.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 01/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

enum FindVersesError: Error {
    case io
    case utf8
    case database
    case fetch
}

class Verse {
    let id: Int32
    let text: String

    init(id: Int32, text: String) {
        self.id = id
        self.text = text
    }

    func toRaw() -> VerseRaw {
        let key = String(id)

        var raw = VerseRaw()
        withUnsafeMutableBytes(of: &raw.key) { ptr in
            key.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }
        withUnsafeMutableBytes(of: &raw.text) { ptr in
            text.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }

        return raw
    }

    class func findVersesByBookAndChapter(translation: String, book: String, chapter: UInt16) throws -> Array<Verse> {
        var verseView = VerseView()
        let retval = verse_find_by_book_and_chapter(translation, &verseView, book, chapter)
        if retval == 0 {
            var verseList = Array<Verse>()
            verseList.reserveCapacity(verseView.count)
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    let key = Int32(String(cString: &verse.key.0))!
                    verseList.append(Verse(id: key, text: String(cString: &verse.text.0)))
                }
            })
            return verseList
        } else {
            switch retval {
            case 1:
                throw FindVersesError.io
            case 9:
                throw FindVersesError.utf8
            case 12:
                throw FindVersesError.database
            default:
                fatalError("unhandled error code \(retval)")
            }
        }
    }

    class func fetchVersesByBookAndChapter(translation: String, source: VerseSource, book: String, chapter: UInt16) throws -> Array<Verse> {
        var verseView = VerseView()
        let retval = verse_fetch_by_book_and_chapter(translation, &verseView, source, book, chapter)
        if retval == 0 {
            var verseList = Array<Verse>()
            withUnsafePointer(to: &verseView.verses.0, { verses in
                for i in 0..<verseView.count {
                    var verse = verses[i]
                    let key = Int32(String(cString: &verse.key.0))!
                    verseList.append(Verse(id: key, text: String(cString: &verse.text.0)))
                }
            })
            return verseList
        } else {
            switch retval {
            case 15:
                throw FindVersesError.fetch
            default:
                fatalError("unhandled error code \(retval)")
            }
        }
    }

    class func insertVersesForBookAndChapter(translation: String, book: String, chapter: UInt16, verses: [Verse]) throws {
        var verseView = VerseView()
        for verse in verses {
            withUnsafeMutablePointer(to: &verseView.verses.0) { ptr in
                ptr.advanced(by: verseView.count).pointee = verse.toRaw()
            }

            verseView.count += 1
        }

        let ret = verse_insert(translation, &verseView, book, chapter)
        switch ret {
        case 0: break // success
        case 1:
            throw SessionError.io
        case 2:
            throw SessionError.sessionExists
        case 3:
            throw SessionError.sessionDataCorrupt
        case 5:
            throw SessionError.sessionTooMany
        case 9:
            throw SessionError.utf8
        case 10:
            throw SessionError.bookUnknown
        case 11:
            throw SessionError.nul
        default:
            fatalError("unhandled error code \(ret)")
        }
    }
}
