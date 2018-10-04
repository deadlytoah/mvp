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

    init(raw: LocationRaw) {
        self.raw = raw
    }
}

enum Level {
    case Easier
    case Easy
    case Normal
    case Hard
    case Harder

    init(raw: UInt8) {
        switch raw {
        case 0:
            self = Level.Easier
        case 1:
            self = Level.Easy
        case 2:
            self = Level.Normal
        case 3:
            self = Level.Hard
        case 4:
            self = Level.Harder
        default:
            fatalError("unknown difficulty level \(raw)")
        }
    }

    func toByte() -> UInt8 {
        switch self {
        case Level.Easier:
            return 0
        case Level.Easy:
            return 1
        case Level.Normal:
            return 2
        case Level.Hard:
            return 3
        case Level.Harder:
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

enum SessionError: Error {
    case io
    case sessionDataCorrupt
    case sessionTooMany
    case sessionExists
    case bufferTooSmall
    case utf8
    case bookUnknown
    case nul
}

class Session {
    var raw: SessionRaw?
    var translation_: String

    var translation: String {
        get {
            return translation_
        }
    }

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
    }
    var strategy: Strategy {
        get {
            return Strategy(raw: raw!.strategy)
        }
    }

    init(raw: SessionRaw) {
        self.raw = raw
        self.translation_ = String(cString: &self.raw!.range.0.translation.0)
    }

    func create() throws {
        let ret = session_create(&self.raw!)
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

    func delete() throws {
        let ret = session_delete(&self.raw!)
        self.raw = nil
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

    class func listSessions() throws -> [Session] {
        var sessionsLen = 20
        var sessionsBuffer = Array(repeating: SessionRaw(), count: sessionsLen)
        try sessionsBuffer.withUnsafeMutableBufferPointer { sessionsPtr in
            let ret = session_list_sessions(sessionsPtr.baseAddress!, &sessionsLen)
            if ret != 0 {
                switch ret {
                case 1:
                    throw SessionError.io
                case 2:
                    throw SessionError.sessionExists
                case 3:
                    throw SessionError.sessionDataCorrupt
                case 4:
                    throw SessionError.bufferTooSmall
                case 5:
                    throw SessionError.sessionTooMany
                case 9:
                    throw SessionError.utf8
                case 11:
                    throw SessionError.nul
                default:
                    fatalError("unhandled error code \(ret)")
                }
            }
        }

        return sessionsBuffer.prefix(sessionsLen).map { rawSession in
            return Session(raw: rawSession)
        }
    }
}
