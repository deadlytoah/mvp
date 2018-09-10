use capi::Result;
use dirs;
use libc::{c_char, c_int};
use model::compat::Verse;
use sdb::Sdb;
use std::ffi::CStr;
use std::mem;

const DB_EXT: &str = ".sdb";

#[repr(C)]
pub struct VerseView {
    next: usize,
    verses: [Verse; 176], // psalm 119 has 176 verses
}

impl VerseView {
    pub fn push(&mut self, verse: Verse) {
        assert!(self.next < self.verses.len());
        self.verses[self.next] = verse;
        self.next += 1;
    }

    pub fn count(&self) -> usize {
        self.next
    }
}

#[no_mangle]
pub unsafe fn verse_find_all(translation: *const c_char, view: *mut VerseView) -> c_int {
    let translation = CStr::from_ptr(translation);
    match imp::verse_find_all(translation, &mut *view) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            1
        }
    }
}

#[no_mangle]
pub unsafe fn verse_find_by_book_and_chapter(
    translation: *const c_char,
    view: *mut VerseView,
    book: *const c_char,
    chapter: u16,
) -> c_int {
    let translation = CStr::from_ptr(translation);
    let book = CStr::from_ptr(book);
    match imp::verse_find_by_book_and_chapter(translation, &mut *view, book, chapter) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            1
        }
    }
}

mod imp {
    use super::*;
    use std::fs;

    pub fn verse_find_all(translation: &CStr, view: &mut VerseView) -> Result<()> {
        let mut dbpath = dirs::data_dir().expect("unable to get platform's data directory.");
        dbpath.push("mvp-speedtype");
        if !dbpath.exists() {
            fs::create_dir(&dbpath)?;
        }

        let translation = translation.to_str()?;
        dbpath.push(&(translation.to_owned() + DB_EXT));
        let dbpath = dbpath.to_str().expect("failed to convert path to string");

        let mut sdb = Sdb::open(&dbpath)?;
        let verse_table = sdb
            .tables_mut()
            .iter_mut()
            .filter(|table| !table.is_dropped())
            .find(|table| table.name() == "verse")
            .expect("verse table");
        verse_table.create_manager()?;
        let manager = verse_table.manager_mut().expect("manager");
        manager.verify()?;
        manager.service()?;
        let records = manager.select_all()?;

        for rec in records {
            if rec["deleted"] == "0" {
                let key = &rec["key"];
                let text = &rec["text"];

                let mut verse: Verse = unsafe { mem::zeroed() };
                let key = key.as_bytes();
                assert!(key.len() <= verse.key.len());
                verse.key[..key.len()].copy_from_slice(key);
                let text = text.as_bytes();
                assert!(text.len() <= verse.text.len());
                verse.text[..text.len()].copy_from_slice(text);

                view.push(verse);
            }
        }
        Ok(())
    }

    pub fn verse_find_by_book_and_chapter(
        translation: &CStr,
        view: &mut VerseView,
        book: &CStr,
        chapter: u16,
    ) -> Result<()> {
        let mut dbpath = dirs::data_dir().expect("unable to get platform's data directory.");
        dbpath.push("mvp-speedtype");
        if !dbpath.exists() {
            fs::create_dir(&dbpath)?;
        }

        let translation = translation.to_str()?;
        dbpath.push(&(translation.to_owned() + DB_EXT));
        let dbpath = dbpath.to_str().expect("failed to convert path to string");

        let mut sdb = Sdb::open(&dbpath)?;
        let verse_table = sdb
            .tables_mut()
            .iter_mut()
            .filter(|table| !table.is_dropped())
            .find(|table| table.name() == "verse")
            .expect("verse table");
        verse_table.create_manager()?;
        let manager = verse_table.manager_mut().expect("manager");
        manager.verify()?;
        manager.service()?;
        let records = manager.select_all()?;

        let book = book.to_str()?;
        let chapter = chapter.to_string();
        let prefix = book.to_owned() + " " + &chapter + ":";

        let mut sortable: Vec<(&String, &String)> = records
            .iter()
            .filter(|rec| rec["deleted"] == "0")
            .filter(|rec| rec["key"].starts_with(&prefix))
            .map(|rec| (&rec["key"], &rec["text"]))
            .collect();
        sortable.sort_unstable_by_key(|rec| {
            let key = rec.0;
            let chapter_verse = key.split_whitespace().nth(1).expect("chapter_verse");
            let verse = chapter_verse.split(':').nth(1).expect("verse");
            verse.parse::<u16>().expect("parse verse")
        });

        for (key, text) in sortable.drain(..) {
            view.verses[view.next].key[..key.len()].copy_from_slice(key.as_bytes());
            view.verses[view.next].text[..text.len()].copy_from_slice(text.as_bytes());
            view.next += 1;
        }

        Ok(())
    }
}
