//
//  AppDelegate.swift
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 01/08/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

import Cocoa

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {



    func applicationDidFinishLaunching(_ aNotification: Notification) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(true, forKey: "DisabledDictationMenuItem")
        userDefaults.set(true, forKey: "DisabledCharacterPaletteMenuItem")
    }

    func applicationWillTerminate(_ aNotification: Notification) {
        // Insert code here to tear down your application
    }


}

