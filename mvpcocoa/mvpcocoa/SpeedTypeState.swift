//
//  SpeedTypeState.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 15/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

class SpeedtypeChar {
    var id: CharId
    var character: Character
    var whitespace: Bool
    var newline: Bool
    var word: WordId?
    var visible: Bool
    var typed: Character?
    var correct: Bool
    var rendered: Bool

    init(raw: SpeedtypeCharRaw) {
        self.id = raw.id
        self.character = Character.init(Unicode.Scalar(raw.character)!)
        self.whitespace = raw.whitespace != 0
        self.newline = raw.newline != 0
        if raw.has_word == 0 {
            self.word = nil
        } else {
            self.word = raw.word
        }
        self.visible = raw.visible != 0
        if raw.has_typed == 0 {
            self.typed = nil
        } else {
            self.typed = Character.init(Unicode.Scalar(raw.typed)!)
        }
        self.correct = raw.correct != 0
        self.rendered = raw.rendered != 0
    }
}

class SpeedtypeWord {
    var id: WordId
    var word: String
    var visible: Bool
    var touched: Bool
    var behind: Bool
    var chars: [CharId]

    init(raw: SpeedtypeWordRaw) {
        self.id = raw.id
        self.word = String(cString: raw.word)
        self.visible = raw.visible != 0
        self.touched = raw.touched != 0
        self.behind = raw.behind != 0
        var chars: [CharId] = []
        for i in 0..<raw.characters_len {
            chars.append(raw.characters_ptr[i])
        }
        self.chars = chars
    }
}

class SpeedtypeSentence {
    var words: [WordId]

    init(raw: SpeedtypeSentenceRaw) {
        var words: [WordId] = []
        for i in 0..<raw.words_len {
            words.append(raw.words_ptr[i])
        }
        self.words = words
    }
}

class SpeedtypeState {
    var buffer: [SpeedtypeChar]
    var words: [SpeedtypeWord]
    var sentences: [SpeedtypeSentence]

    init(raw: SpeedtypeStateRaw) {
        var buffer: [SpeedtypeChar] = []
        for i in 0..<raw.buffer_len {
            let char = SpeedtypeChar(raw: raw.buffer_ptr[i])
            buffer.append(char)
        }
        self.buffer = buffer
        
        var words: [SpeedtypeWord] = []
        for i in 0..<raw.words_len {
            let word = SpeedtypeWord(raw: raw.words_ptr[i])
            words.append(word)
        }
        self.words = words
        
        var sentences: [SpeedtypeSentence] = []
        for i in 0..<raw.sentences_len {
            let sentence = SpeedtypeSentence(raw: raw.sentences_ptr[i])
            sentences.append(sentence)
        }
        self.sentences = sentences
    }
}
