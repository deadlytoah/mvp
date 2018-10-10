//
//  Session.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 04/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

class Location {
    var raw: LocationRaw

    var translation: String {
        get {
            return String(cString: &raw.translation.0)
        }
    }

    var book: String {
        get {
            return String(cString: &raw.book.0)
        }
    }

    var chapter: UInt16 {
        get {
            return raw.chapter
        }
    }

    var sentence: UInt16 {
        get {
            return raw.sentence
        }
    }

    var verse: UInt16 {
        get {
            return raw.verse
        }
    }

    init(translation: String, book: String, chapter: UInt16, sentence: UInt16, verse: UInt16) {
        self.raw = LocationRaw()
        withUnsafeMutableBytes(of: &self.raw.translation) { ptr in
            translation.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }
        withUnsafeMutableBytes(of: &self.raw.book) { ptr in
            book.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }
        self.raw.chapter = chapter
        self.raw.sentence = sentence
        self.raw.verse = verse
    }

    init(raw: LocationRaw) {
        self.raw = raw
    }
}

enum Level {
    case Easiest
    case Easy
    case Normal
    case Hard
    case Hardest

    init(raw: UInt8) {
        switch raw {
        case 0:
            self = Level.Easiest
        case 1:
            self = Level.Easy
        case 2:
            self = Level.Normal
        case 3:
            self = Level.Hard
        case 4:
            self = Level.Hardest
        default:
            fatalError("unknown difficulty level \(raw)")
        }
    }

    func toByte() -> UInt8 {
        switch self {
        case Level.Easiest:
            return 0
        case Level.Easy:
            return 1
        case Level.Normal:
            return 2
        case Level.Hard:
            return 3
        case Level.Hardest:
            return 4
        }
    }
}

enum Strategy {
    case Simple
    case FocusedLearning

    init(raw: UInt8) {
        switch raw {
        case 0:
            self = Strategy.Simple
        case 1:
            self = Strategy.FocusedLearning
        default:
            fatalError("unknown strategy \(raw)")
        }
    }

    func toByte() -> UInt8 {
        switch self {
        case Strategy.Simple:
            return 0
        case Strategy.FocusedLearning:
            return 1
        }
    }
}

class Session {
    var raw: SessionRaw?

    var name: String {
        get {
            return String(cString: &raw!.name.0)
        }
    }

    var range: (Location, Location) {
        get {
            let start = Location(raw: raw!.range.0)
            let end = Location(raw: raw!.range.1)
            return (start, end)
        }
    }

    var level: Level {
        get {
            return Level(raw: raw!.level)
        }
        set {
            self.raw!.level = newValue.toByte()
        }
    }

    var strategy: Strategy {
        get {
            return Strategy(raw: raw!.strategy)
        }
    }

    init(raw: SessionRaw) {
        self.raw = raw
    }

    init(name: String, range: (Location, Location), level: Level, strategy: Strategy) {
        self.raw = SessionRaw()
        withUnsafeMutableBytes(of: &self.raw!.name) { ptr in
            name.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }
        self.raw!.range = (range.0.raw, range.1.raw)
        self.raw!.level = level.toByte()
        self.raw!.strategy = strategy.toByte()
    }

    func create() throws {
        let ret = session_create(&self.raw!)
        switch ret {
        case 0: break // success
        default:
            throw CoreLibError.init(rawValue: ret)!
        }
    }

    func delete() throws {
        let ret = session_delete(&self.raw!)
        self.raw = nil
        switch ret {
        case 0: break // success
        default:
            throw CoreLibError.init(rawValue: ret)!
        }
    }

    class func listSessions() throws -> [Session] {
        var sessionsLen = 20
        var sessionsBuffer = Array(repeating: SessionRaw(), count: sessionsLen)
        try sessionsBuffer.withUnsafeMutableBufferPointer { sessionsPtr in
            let ret = session_list_sessions(sessionsPtr.baseAddress!, &sessionsLen)
            switch ret {
            case 0: break // success
            default:
                throw CoreLibError.init(rawValue: ret)!
            }
        }

        return sessionsBuffer.prefix(sessionsLen).map { rawSession in
            return Session(raw: rawSession)
        }
    }
}
