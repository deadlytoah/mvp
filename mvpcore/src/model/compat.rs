use capi::Result;
use model::strong::Book;
use model::strong;
use std::ffi::{CStr, CString};
use std::str;

#[derive(Deserialize, Serialize)]
#[repr(C)]
pub struct Session {
    pub name: [u8; 32],
    pub range: [Location; 2],
    pub level: u8,
    pub strategy: u8,
}

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
