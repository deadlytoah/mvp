use capi::{self, Result};
use dirs;
use libc::{c_char, c_int};
use model::compat::Verse;
use model::strong;
use regex::Regex;
use sdb::tables::Record;
use sdb::Sdb;
use std::ffi::{CStr, CString};
use std::fmt::{self, Display, Formatter};

const DB_EXT: &str = ".sdb";

static SOURCES: &[SourceDescription] = &[SourceDescription {
    id: VerseSource::BlueLetterBible,
    name: "Blue Letter Bible",
    form_url: "https://www.blueletterbible.org/tools/MultiVerse.cfm",
}];

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

#[derive(Debug)]
pub enum FetchError {
    HttpRequest(::reqwest::Error),
    Regex(::regex::Error),
    RegexMismatch(String),
    ParseInt(::std::num::ParseIntError),
}

impl ::std::error::Error for FetchError {
    fn description(&self) -> &str {
        match *self {
            FetchError::HttpRequest(ref e) => e.description(),
            FetchError::Regex(ref e) => e.description(),
            FetchError::RegexMismatch(_) => "the text did not match the regex",
            FetchError::ParseInt(ref e) => e.description(),
        }
    }

    fn cause(&self) -> Option<&::std::error::Error> {
        match *self {
            FetchError::HttpRequest(ref e) => Some(e),
            FetchError::Regex(ref e) => Some(e),
            FetchError::RegexMismatch(_) => None,
            FetchError::ParseInt(ref e) => Some(e),
        }
    }
}

impl Display for FetchError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match *self {
            FetchError::HttpRequest(ref e) => write!(f, "error making an HTTP request: {}", e),
            FetchError::Regex(ref e) => write!(f, "regex error: {}", e),
            FetchError::RegexMismatch(ref s) => {
                write!(f, "the text did not match the regex: [{}]", s)
            }
            FetchError::ParseInt(ref e) => write!(f, "parse integer error: {}", e),
        }
    }
}

impl From<reqwest::Error> for FetchError {
    fn from(err: reqwest::Error) -> FetchError {
        FetchError::HttpRequest(err)
    }
}

impl From<regex::Error> for FetchError {
    fn from(err: regex::Error) -> FetchError {
        FetchError::Regex(err)
    }
}

impl From<::std::num::ParseIntError> for FetchError {
    fn from(err: ::std::num::ParseIntError) -> FetchError {
        FetchError::ParseInt(err)
    }
}

#[no_mangle]
pub unsafe fn verse_find_all(translation: *const c_char, view: *mut VerseView) -> c_int {
    let translation = CStr::from_ptr(translation);
    match imp::verse_find_all(translation, &mut *view) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            capi::map_error_to_code(&e) as c_int
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
            capi::map_error_to_code(&e) as c_int
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
            capi::map_error_to_code(&e.into()) as c_int
        }
    }
}

#[no_mangle]
pub unsafe fn verse_insert(
    translation: *const c_char,
    view: *const VerseView,
    book: *const c_char,
    chapter: u16,
) -> c_int {
    let translation = CStr::from_ptr(translation);
    let book = CStr::from_ptr(book);
    match imp::verse_insert(translation, &*view, &book, chapter) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            capi::map_error_to_code(&e) as c_int
        }
    }
}

#[no_mangle]
pub unsafe fn cache_create(translation: *const c_char) -> c_int {
    let translation = CStr::from_ptr(translation);
    match imp::cache_create(translation) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            capi::map_error_to_code(&e) as c_int
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

        let mut sortable: Vec<_> = records
            .iter()
            .filter(|rec| rec["deleted"] == "0")
            .filter(|rec| rec["key"].starts_with(&prefix))
            .map(|rec| (rec["key"].as_str(), rec["text"].as_str()))
            .map(|(key, text)| {
                let chapter_verse = key
                    .split_whitespace()
                    .nth(1)
                    .expect("missing chapter and verse number");
                let verse_num = chapter_verse
                    .split(':')
                    .nth(1)
                    .expect("missing verse number");
                (verse_num, text)
            })
            .collect();
        sortable
            .sort_unstable_by_key(|rec| rec.0.parse::<u16>().expect("failed parsing verse number"));

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
    ) -> ::std::result::Result<(), FetchError> {
        let translation = translation.to_str().expect("utf8 error");
        let book = book.to_str().expect("utf8 error");
        let _ = strong::Book::from_short_name(&book).expect("unknown book error");
        let source = SOURCES
            .iter()
            .find(|s| s.id == source)
            // Panic as this is certainly a bug.
            .expect("source not found");

        let client = reqwest::Client::new();
        let form = reqwest::multipart::Form::new()
            .text("t", translation.to_string())
            .text("mvText", [book.to_string(), chapter.to_string()].join(" "));
        let mut res = client.post(source.form_url).multipart(form).send()?;
        let body = res.text()?;

        let re_outer = Regex::new(r#"<div id="multiResults">\[.*:.*-([0-9]+) .*\](.*)</div>"#)?;
        let cap = re_outer
            .captures(&body)
            .ok_or_else(|| FetchError::RegexMismatch(re_outer.to_string()))?;
        let count = cap[1].parse::<usize>()?;
        let verses = &cap[2];

        // we can structurise our capture better if we know the number
        // of verses.
        let mut pattern = String::new();
        pattern.extend(
            (0..count)
                .map(|i| format!(" ({}) (.*)", 1 + i))
                .collect::<Vec<_>>(),
        );
        let re_inner = Regex::new(&pattern)?;
        let cap = re_inner
            .captures(&verses)
            .ok_or_else(|| FetchError::RegexMismatch(pattern))?;
        for i in 0..count {
            let (key, text) = (&cap[i * 2 + 1], &cap[i * 2 + 2]);
            view.push(key, text);
        }
        Ok(())
    }

    pub fn verse_insert(
        translation: &CStr,
        view: &VerseView,
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

        let key_prefix = [book.to_str().expect("utf8 error"), &chapter.to_string()].join(" ");

        for i in 0..view.next {
            let mut rec = Record::new();
            let verse = &view.verses[i];

            let key = unsafe { CStr::from_ptr(verse.key.as_ptr() as *const i8) };
            let key = key.to_str().expect("utf8 error");
            let key = [&key_prefix, key].join(":");
            rec.insert("key".into(), key);

            let text = unsafe { CStr::from_ptr(verse.text.as_ptr() as *const i8) };
            let text = text.to_str().expect("utf8 error");
            rec.insert("text".into(), text.into());

            rec.insert("deleted".into(), "0".into());

            manager.insert(rec)?;
        }

        Ok(())
    }

    pub fn cache_create(translation: &CStr) -> Result<()> {
        let mut dbpath = dirs::data_dir().expect("unable to get platform's data directory.");
        dbpath.push("mvp-speedtype");
        if !dbpath.exists() {
            fs::create_dir(&dbpath)?;
        }

        let translation = translation.to_str()?;
        dbpath.push(&(translation.to_owned() + DB_EXT));
        let dbpath = dbpath.to_str().expect("failed to convert path to string");
        Sdb::create(&dbpath)?;

        let mut sdb = Sdb::open(&dbpath)?;
        sdb.create_table("verse.mjson")?;

        Ok(())
    }
}
