use capi::Result;
use dirs;
use libc::{c_char, c_int};
use model::compat::Verse;
use model::strong;
use regex::Regex;
use sdb::Sdb;
use std::ffi::{CStr, CString};

const DB_EXT: &str = ".sdb";

#[repr(C)]
pub struct VerseView {
    next: usize,
    verses: [Verse; 176], // psalm 119 has 176 verses
}

impl VerseView {
    pub fn push(&mut self, key: &str, text: &str) {
        assert!(self.next < self.verses.len());
        let verse = &mut self.verses[self.next];
        let key = CString::new(key).expect("nul error");
        let key = key.as_bytes_with_nul();
        let text = CString::new(text).expect("nul error");
        let text = text.as_bytes_with_nul();
        verse.key[..key.len()].copy_from_slice(key);
        verse.text[..text.len()].copy_from_slice(text);
        self.next += 1;
    }

    pub fn count(&self) -> usize {
        self.next
    }
}

#[derive(Clone, Copy, PartialEq)]
#[repr(C)]
pub enum VerseSource {
    BlueLetterBible,
}

pub struct SourceDescription {
    id: VerseSource,
    #[allow(dead_code)]
    name: &'static str,
    form_url: &'static str,
}

static SOURCES: &[SourceDescription] = &[SourceDescription {
    id: VerseSource::BlueLetterBible,
    name: "Blue Letter Bible",
    form_url: "https://www.blueletterbible.org/tools/MultiVerse.cfm",
}];

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

#[no_mangle]
pub unsafe fn verse_fetch_by_book_and_chapter(
    translation: *const c_char,
    view: *mut VerseView,
    source: VerseSource,
    book: *const c_char,
    chapter: u16,
) -> c_int {
    let translation = CStr::from_ptr(translation);
    let book = CStr::from_ptr(book);
    match imp::verse_fetch_by_book_and_chapter(translation, &mut *view, source, &book, chapter) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            1
        }
    }
}

mod imp {
    use super::*;
    use reqwest;
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
                view.push(&rec["key"], &rec["text"]);
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
            view.push(key, text);
        }

        Ok(())
    }

    pub fn verse_fetch_by_book_and_chapter(
        translation: &CStr,
        view: &mut VerseView,
        source: VerseSource,
        book: &CStr,
        chapter: u16,
    ) -> Result<()> {
        let translation = translation.to_string_lossy();
        let book = book.to_string_lossy();
        let _ = strong::Book::from_short_name(&book)?;
        let source = SOURCES
            .iter()
            .find(|s| s.id == source)
            .expect("source not found");

        let client = reqwest::Client::new();
        let form = reqwest::multipart::Form::new()
            .text("t", translation.to_string())
            .text("mvText", [book.to_string(), chapter.to_string()].join(" "));
        let mut res = client
            .post(source.form_url)
            .multipart(form)
            .send()
            .expect("failed to post a http request");
        let body = res.text().expect("failed to get http response body text");

        let re_outer = Regex::new(r#"<div id="multiResults">\[.*:.*-([0-9]+) .*\](.*)</div>"#)
            .expect("can't create regex");
        let cap = re_outer.captures(&body).expect("capture failed");
        let count = cap[1].parse::<usize>().expect("int parse failed");
        let verses = &cap[2];

        // we can structurise our capture better if we know the number
        // of verses.
        let mut pattern = String::new();
        pattern.extend(
            (0..count)
                .map(|i| format!(" ({}) (.*)", 1 + i))
                .collect::<Vec<_>>(),
        );
        let re_inner = Regex::new(&pattern).expect("can't create regex");
        let cap = re_inner.captures(&verses).expect("capture failed");
        for i in 0..count {
            let (key, text) = (&cap[i * 2 + 1], &cap[i * 2 + 2]);
            view.push(key, text);
        }
        Ok(())
    }
}
