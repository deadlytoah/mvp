//
//  GraphLayout.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 25/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

func graphLayout(text: String) -> Array<String> {
    let cstr = text.cString(using: String.Encoding.utf8)!
    var buffer: [LayoutLine]
    var len: size_t = 8
    var retcode: Int32 = 0

    repeat {
        // starts with 16, doubling every time we run out of space in buffer
        len *= 2
        buffer = Array.init(repeating: LayoutLine(index: 0, length: 0), count: len)
        retcode = graphlayout_layout(cstr, &buffer, &len)
    } while retcode != 0

    var strArray: [String] = []
    for i in 0..<len {
        let layoutLine = buffer[i]
        cstr[layoutLine.index..<layoutLine.index + layoutLine.length].withUnsafeBytes({ bytes in
            strArray.append(String(bytes: bytes, encoding: String.Encoding.utf8)!)
        })
    }
    return strArray
}
