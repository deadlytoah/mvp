//
//  Sentence.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 02/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

class Sentence {
    let text: String

    init(text: String) {
        self.text = text
    }

    class func sentencesFromVerses(verses: Array<String>) -> Array<Sentence> {
        // allocate a buffer that should big enough in size.
        let utf8s = verses.map { str in
            str.utf8
        }
        let lengths = utf8s.map { str in
            // Take into account the terminating null chars.
            str.count + 1
        }
        let bufferSize = lengths.reduce(0) { (bufferSize, length) in
                return bufferSize + length
        }

        var cstrBuffer = Array<UInt8>()
        cstrBuffer.reserveCapacity(bufferSize)
        for utf8 in utf8s {
            cstrBuffer.append(contentsOf: utf8)
            cstrBuffer.append(0)
        }

        // Now we need the list of offsets into the buffer.  With
        // this list we can construct the list of C string pointers
        // to pass to the Rust function.
        var offsets = lengths.enumerated().flatMap { args -> [Int] in
            let (i, length) = args
            if i == 0 {
                return [0, length]
            } else {
                return [length]
            }
        }
        _ = offsets.popLast()!
        assert(offsets.count == utf8s.count)

        // we seem to miss scan() in the Swift standard library.
        for i in 0..<offsets.count {
            if i != 0 {
                offsets[i] = offsets[i - 1] + offsets[i]
            }
        }

        return cstrBuffer.withUnsafeBytes { ptr in
            var cstrArg = Array<UnsafePointer<Int8>?>()
            cstrArg.reserveCapacity(utf8s.count)
            for offset in offsets {
                cstrArg.append(ptr.baseAddress?.advanced(by: offset).assumingMemoryBound(to: Int8.self))
            }

            var bufferLen = 1024
            var buffer = Array(repeating: SentenceRaw(), count: bufferLen)
            cstrArg.withUnsafeMutableBufferPointer { versesPtr in
                buffer.withUnsafeMutableBufferPointer { bufferPtr in
                    sentences_from_verses(versesPtr.baseAddress!, verses.count, bufferPtr.baseAddress!, &bufferLen)
                }
            }

            return buffer.prefix(upTo: bufferLen).map { raw in
                var r = raw
                return Sentence(text: String(cString: &r.text.0))
            }
       }
    }
}
