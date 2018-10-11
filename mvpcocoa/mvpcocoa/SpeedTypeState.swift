//
//  SpeedTypeState.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 15/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

class SpeedTypeChar {
    var raw: UnsafeMutablePointer<SpeedTypeCharRaw>

    var id: CharId {
        get {
            return raw.pointee.id
        }
    }

    var character: Character {
        get {
            return Character.init(Unicode.Scalar(raw.pointee.character)!)
        }
    }

    var whitespace: Bool {
        get {
            return raw.pointee.whitespace != 0
        }
    }

    var newline: Bool {
        get {
            return raw.pointee.newline != 0
        }
    }

    var word: WordId? {
        get {
            if raw.pointee.has_word == 0 {
                return nil
            } else {
                return raw.pointee.word
            }
        }
    }

    var visible: Bool {
        get {
            return raw.pointee.visible != 0
        }
    }

    var typed: Character? {
        get {
            if raw.pointee.has_typed == 0 {
                return nil
            } else {
                return Character.init(Unicode.Scalar(raw.pointee.typed)!)
            }
        }
        set {
            if let typed = newValue {
                raw.pointee.has_typed = 1
                raw.pointee.typed = typed.unicodeScalars.first!.value
            } else {
                raw.pointee.has_typed = 0
            }
        }
    }

    var correct: Bool {
        get {
            return raw.pointee.correct != 0
        }
        set {
            raw.pointee.correct = newValue ? 1 : 0
        }
    }

    var rendered: Bool {
        get {
            return self.raw.pointee.rendered != 0
        }
        set {
            self.raw.pointee.rendered = newValue ? 1 : 0
        }
    }

    init(raw: UnsafeMutablePointer<SpeedTypeCharRaw>) {
        self.raw = raw
    }
}

class SpeedTypeWord {
    var raw: UnsafeMutablePointer<SpeedTypeWordRaw>

    var id: WordId {
        get {
            return raw.pointee.id
        }
    }

    var word: String {
        get {
            return String(cString: raw.pointee.word)
        }
    }

    var visible: Bool {
        get {
            return raw.pointee.visible != 0
        }
    }

    var touched: Bool {
        get {
            return raw.pointee.touched != 0
        }
        set {
            raw.pointee.touched = newValue ? 1 : 0
        }
    }

    var behind: Bool {
        get {
            return raw.pointee.behind != 0
        }
        set {
            raw.pointee.behind = newValue ? 1 : 0
        }
    }

    var chars: [CharId] {
        get {
            var chars: [CharId] = []
            for i in 0..<raw.pointee.characters_len {
                chars.append(raw.pointee.characters_ptr[i])
            }
            return chars
        }
    }

    init(raw: UnsafeMutablePointer<SpeedTypeWordRaw>) {
        self.raw = raw
    }
}

class SpeedTypeSentence {
    let raw: UnsafeMutablePointer<SpeedTypeSentenceRaw>

    var words: [WordId] {
        get {
            var words: [WordId] = []
            for i in 0..<raw.pointee.words_len {
                words.append(raw.pointee.words_ptr[i])
            }
            return words
        }
    }

    init(raw: UnsafeMutablePointer<SpeedTypeSentenceRaw>) {
        self.raw = raw
    }
}

class SpeedTypeState {
    var raw: UnsafeMutablePointer<SpeedTypeStateRaw>

    var buffer: [SpeedTypeChar] {
        get {
            var buffer: [SpeedTypeChar] = []
            for i in 0..<raw.pointee.buffer_len {
                let char = SpeedTypeChar(raw: raw.pointee.buffer_ptr.advanced(by: i))
                buffer.append(char)
            }
            return buffer
        }
    }

    var words: [SpeedTypeWord] {
        get {
            var words: [SpeedTypeWord] = []
            for i in 0..<raw.pointee.words_len {
                let word = SpeedTypeWord(raw: raw.pointee.words_ptr.advanced(by: i))
                words.append(word)
            }
            return words
        }
    }

    var sentences: [SpeedTypeSentence] {
        get {
            var sentences: [SpeedTypeSentence] = []
            for i in 0..<raw.pointee.sentences_len {
                let sentence = SpeedTypeSentence(raw: raw.pointee.sentences_ptr.advanced(by: i))
                sentences.append(sentence)
            }
            return sentences
        }
    }

    init(raw: UnsafeMutablePointer<SpeedTypeStateRaw>) {
        self.raw = raw
    }

    init() {
        self.raw = speedtype_new()
    }

    deinit {
        speedtype_delete(self.raw)
    }

    func processLine(_ line: String) throws {
        let ret = speedtype_process_line(self.raw, line)
        if ret != 0 {
            throw CoreLibError(rawValue: ret)!
        }
    }

    func applyLevel(_ level: UInt8) {
        speedtype_apply_level(self.raw, level)
    }
}
