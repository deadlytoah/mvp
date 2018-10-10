//
//  Error.swift
//  mvpcocoa
//
//  Created by Heesuk Shin on 10/10/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Foundation

enum CoreLibError: Int32, Error {
    case io = 1
    case sessionExists
    case sessionDataCorrupt
    case sessionBufferTooSmall
    case sessionTooMany
    case rangeParse
    case levelUnknown
    case strategyUnknown
    case utf8
    case bookUnknown
    case nul
    case database
    case httpRequest
    case regex
    case fetch
}
