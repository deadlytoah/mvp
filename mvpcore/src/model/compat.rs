use capi::Result;
use model::strong;
use model::strong::Book;
use std::ffi::{CStr, CString};
use std::mem;
use std::str;

#[derive(Deserialize, Serialize)]
#[repr(C)]
pub struct Location {
    pub translation: [u8; 8],
    pub book: [u8; 8],
    pub chapter: u16,
    pub sentence: u16,
    pub verse: u16,
}

impl Location {
    pub fn to_strong_typed(&self) -> Result<strong::Location> {
        let translation = unsafe { CStr::from_ptr(self.translation.as_ptr() as *const i8) };
        let translation = translation.to_str()?;
        let book = unsafe { CStr::from_ptr(self.book.as_ptr() as *const i8) };
        let book = book.to_str()?;
        let book = Book::from_short_name(book)?;
        let chapter = self.chapter;
        let sentence = self.sentence;
        let verse = self.verse;
        Ok(strong::Location {
            translation: translation.into(),
            book,
            chapter,
            sentence,
            verse,
        })
    }

    pub fn copy_from_strong_typed(&mut self, loc: &strong::Location) -> Result<()> {
        self.chapter = loc.chapter;
        self.sentence = loc.sentence;
        self.verse = loc.verse;

        let translation = CString::new(loc.translation.clone())?;
        let translation = translation.as_bytes_with_nul();
        self.translation[..translation.len()].copy_from_slice(translation);

        let book = loc.book.short_name();
        let book = CString::new(book)?;
        let book = book.as_bytes_with_nul();
        self.book[..book.len()].copy_from_slice(book);

        Ok(())
    }
}

#[repr(C)]
pub struct Verse {
    pub key: [u8; 16],
    pub text: [u8; 256],
}

#[derive(Copy, Clone)]
#[repr(C)]
pub struct Sentence {
    text: [u8; 1024],
}

impl Sentence {
    pub fn copy_from(&mut self, from: strong::Sentence) {
        let text = CString::new(from.text).expect("nul in string");
        let text = text.as_bytes_with_nul();
        self.text[..text.len()].copy_from_slice(text);
    }
}

impl From<strong::Sentence> for Sentence {
    fn from(from: strong::Sentence) -> Self {
        let mut sentence = Sentence {
            text: unsafe { mem::zeroed() },
        };

        let text = CString::new(from.text).expect("nul in string");
        let text = text.as_bytes_with_nul();
        sentence.text[..text.len()].copy_from_slice(text);

        sentence
    }
}
