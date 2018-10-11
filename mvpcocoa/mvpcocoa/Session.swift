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

enum Level: UInt8 {
    case Easiest
    case Easy
    case Normal
    case Hard
    case Hardest
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
    // Always owns the contents of the raw object.
    var raw: SessionRaw

    var name: String {
        get {
            return String(cString: &raw.name.0)
        }
    }

    var range: (Location, Location) {
        get {
            let start = Location(raw: raw.range.0)
            let end = Location(raw: raw.range.1)
            return (start, end)
        }
    }

    var level: Level {
        get {
            return Level(rawValue: raw.level)!
        }
        set {
            self.raw.level = newValue.rawValue
        }
    }

    var strategy: Strategy {
        get {
            return Strategy(raw: raw.strategy)
        }
    }

    var state: SpeedTypeState? {
        get {
            if raw.has_state != 0 {
                return SpeedTypeState(ref: raw.state)
            } else {
                return nil
            }
        }
    }

    var stateMove: SpeedTypeState? {
        get {
            if raw.has_state != 0 {
                let newState = raw.state!
                raw.has_state = 0
                raw.state = nil
                return SpeedTypeState(owned: newState)
            } else {
                return nil
            }
        }
        set {
            if self.raw.has_state != 0 {
                // keep it simple and don't allow self-assignment
                assert(self.raw.state != newValue?.raw)
                speedtype_delete(self.raw.state)
            }

            if let newState = newValue {
                self.raw.has_state = 1
                self.raw.state = newState.raw
                newState.owned = false
            } else {
                self.raw.has_state = 0
                self.raw.state = nil
            }
        }
    }

    init(raw: SessionRaw) {
        self.raw = raw
    }

    init(name: String, range: (Location, Location), level: Level, strategy: Strategy) {
        self.raw = SessionRaw()
        withUnsafeMutableBytes(of: &self.raw.name) { ptr in
            name.utf8CString.withUnsafeBytes { cstr in
                ptr.copyMemory(from: cstr)
            }
        }
        self.raw.range = (range.0.raw, range.1.raw)
        self.raw.level = level.rawValue
        self.raw.strategy = strategy.toByte()
        self.raw.has_state = 0
    }

    deinit {
        if self.raw.has_state != 0 {
            speedtype_delete(self.raw.state)
        }
    }

    func create() throws {
        let ret = session_create(&self.raw)
        switch ret {
        case 0: break // success
        default:
            throw CoreLibError.init(rawValue: ret)!
        }
    }

    func delete() throws {
        let ret = session_delete(&self.raw)
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
