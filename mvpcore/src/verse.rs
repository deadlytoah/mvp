use capi::Result;
use libc::{c_char, c_int};
use sdb::Sdb;
use std::ffi::CStr;
use std::mem;

const DB_EXT: &str = ".sdb";

#[repr(C)]
pub struct Verse {
    key: [u8; 16],
    text: [u8; 256],
}

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

mod imp {
    use super::*;

    pub fn verse_find_all(translation: &CStr, view: &mut VerseView) -> Result<()> {
        let translation = translation.to_str()?;
        let mut sdb = Sdb::open(&(translation.to_owned() + DB_EXT))?;
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
}
