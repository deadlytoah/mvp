use book::Book;
use level::Level;
use libc::*;
use location;
use range::Range;
use session::Session;
use std::boxed::Box;
use std::ffi::{CStr, CString};
use std::mem;
use std::slice;
use strategy::Strategy;

#[repr(C)]
pub struct Location {
    pub translation: [u8; 8],
    pub book: [u8; 8],
    pub chapter: u16,
    pub sentence: u16,
    pub verse: u16,
}

#[repr(C)]
pub enum SessionError {
    OK,
    SessionExists,
    SessionCorruptData,
    SessionWriteError,
    SessionBufferTooSmall,
    RangeParseError,
    LevelUnknown,
    StrategyUnknown,
}

static ERROR_MESSAGES: &'static [&'static str] = &[
    "success\0",
    "session with that name already exists\0",
    "session data file is corrupt\0",
    "error writing the session on disk\0",
    "error parsing the range\0",
    "unknown level\0",
    "unknown strategy\0",
];

#[no_mangle]
pub unsafe fn session_new(name: *const c_char) -> *mut Session {
    let name = CStr::from_ptr(name).to_string_lossy();
    let session = Box::new(Session::named(&name));
    Box::into_raw(session)
}

#[no_mangle]
pub unsafe fn session_delete(session: *mut Session) {
    Box::from_raw(session);
}

/// Writes the session to disk and deletes it.
#[no_mangle]
pub unsafe fn session_write(session: *mut Session) -> c_int {
    let session = Box::from_raw(session);
    if session.write().is_ok() {
        SessionError::OK as c_int
    } else {
        SessionError::SessionWriteError as c_int
    }
}

#[no_mangle]
pub unsafe fn session_set_range(
    session: *mut Session,
    start: *const Location,
    end: *const Location,
) -> c_int {
    let book = if let Ok(book) = CStr::from_bytes_with_nul(&(*start).book) {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let book = if let Ok(book) = book.to_str() {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let book = if let Some(book) = Book::from_short_name(book) {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let translation = if let Ok(translation) = CStr::from_bytes_with_nul(&(*start).translation) {
        translation
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let translation = if let Ok(translation) = translation.to_str() {
        translation
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let s = location::Location {
        translation: translation.into(),
        book,
        chapter: (*start).chapter,
        sentence: (*start).sentence,
        verse: (*start).verse,
    };

    let book = if let Ok(book) = CStr::from_bytes_with_nul(&(*end).book) {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let book = if let Ok(book) = book.to_str() {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let book = if let Some(book) = Book::from_short_name(book) {
        book
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let translation = if let Ok(translation) = CStr::from_bytes_with_nul(&(*end).translation) {
        translation
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let translation = if let Ok(translation) = translation.to_str() {
        translation
    } else {
        return SessionError::RangeParseError as c_int;
    };
    let e = location::Location {
        translation: translation.into(),
        book,
        chapter: (*end).chapter,
        sentence: (*end).sentence,
        verse: (*end).verse,
    };

    let mut session = Box::from_raw(session);
    session.range = Range { start: s, end: e };
    Box::into_raw(session);
    SessionError::OK as c_int
}

#[no_mangle]
pub unsafe fn session_set_level(session: *mut Session, level: c_int) -> c_int {
    if level < Level::Level1 as c_int || level > Level::Level5 as c_int {
        SessionError::LevelUnknown as c_int
    } else {
        let mut session = Box::from_raw(session);
        let level: Level = mem::transmute(level as u8);
        session.level = level;
        Box::into_raw(session);
        SessionError::OK as c_int
    }
}

#[no_mangle]
pub unsafe fn session_set_strategy(session: *mut Session, strategy: c_int) -> c_int {
    if strategy < Strategy::Simple as c_int || strategy > Strategy::FocusedLearning as c_int {
        SessionError::StrategyUnknown as c_int
    } else {
        let mut session = Box::from_raw(session);
        let strategy: Strategy = mem::transmute(strategy as u8);
        session.strategy = strategy;
        Box::into_raw(session);
        SessionError::OK as c_int
    }
}

/// Loads from disk the list of names of all sessions.  The returned
/// list is a sequence of null terminated strings stored back to back
/// in the memory.
#[no_mangle]
pub unsafe fn session_list_sessions(buf: *mut c_char, len: *mut size_t) -> c_int {
    if let Ok(session_seq) = Session::load_all_sessions() {
        let bufsize = *len as usize;
        let mut actual_len = 0usize;
        let mut offset = 0isize;

        for session in session_seq {
            if let Ok(sessname) = CString::new(session.name) {
                let bufslice = slice::from_raw_parts_mut(buf.offset(offset) as *mut u8, bufsize);
                let namebytes = sessname.as_bytes_with_nul();
                bufslice.copy_from_slice(namebytes);
                offset += namebytes.len() as isize;
                actual_len += namebytes.len();

                if actual_len > bufsize {
                    return SessionError::SessionBufferTooSmall as c_int;
                }
            } else {
                return SessionError::SessionCorruptData as c_int;
            };
        }

        *len = actual_len;

        SessionError::OK as c_int
    } else {
        SessionError::SessionCorruptData as c_int
    }
}

#[no_mangle]
pub fn session_get_message(error_code: c_int) -> *const c_char {
    ERROR_MESSAGES[error_code as usize].as_ptr() as *const c_char
}
