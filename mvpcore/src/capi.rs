use book::{Book, BookError};
use level::Level;
use libc::*;
use location;
use range::Range;
use session::{self, Session};
use std::boxed::Box;
use std::ffi::{self, CStr, CString};
use std::fmt::{self, Display, Formatter};
use std::mem;
use std::slice;
use std::str;
use strategy::Strategy;

type Result<T> = ::std::result::Result<T, CapiError>;

#[derive(Debug)]
pub enum CapiError {
    Book(BookError),
    Session(session::SessionError),
    Utf8(str::Utf8Error),
    FromBytesWithNul(ffi::FromBytesWithNulError),
}

impl ::std::error::Error for CapiError {
    fn description(&self) -> &str {
        match *self {
            CapiError::Book(ref e) => e.description(),
            CapiError::Session(ref e) => e.description(),
            CapiError::Utf8(ref e) => e.description(),
            CapiError::FromBytesWithNul(ref e) => e.description(),
        }
    }

    fn cause(&self) -> Option<&::std::error::Error> {
        match *self {
            CapiError::Book(ref e) => Some(e),
            CapiError::Session(ref e) => Some(e),
            CapiError::Utf8(ref e) => Some(e),
            CapiError::FromBytesWithNul(ref e) => Some(e),
        }
    }
}

impl Display for CapiError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match *self {
            CapiError::Book(ref e) => write!(f, "book error: {}", e),
            CapiError::Session(ref e) => write!(f, "session error: {}", e),
            CapiError::Utf8(ref e) => write!(f, "utf8 error: {}", e),
            CapiError::FromBytesWithNul(ref e) => write!(f, "string conversion error: {}", e),
        }
    }
}

impl From<BookError> for CapiError {
    fn from(err: BookError) -> CapiError {
        CapiError::Book(err)
    }
}

impl From<session::SessionError> for CapiError {
    fn from(err: session::SessionError) -> CapiError {
        CapiError::Session(err)
    }
}

impl From<str::Utf8Error> for CapiError {
    fn from(err: str::Utf8Error) -> CapiError {
        CapiError::Utf8(err)
    }
}

impl From<ffi::FromBytesWithNulError> for CapiError {
    fn from(err: ffi::FromBytesWithNulError) -> CapiError {
        CapiError::FromBytesWithNul(err)
    }
}

#[repr(C)]
pub enum SessionError {
    OK,
    IOError,
    SessionExists,
    SessionCorruptData,
    SessionBufferTooSmall,
    SessionTooMany,
    RangeParseError,
    LevelUnknown,
    StrategyUnknown,
    Utf8Error,
    BookUnknown,
    StringConvertError,
}

fn map_error_to_code(error: &CapiError) -> SessionError {
    match *error {
        CapiError::Book(ref e) => match *e {
            BookError::UnknownBook { .. } => SessionError::BookUnknown,
        },
        CapiError::Session(ref e) => match *e {
            session::SessionError::Io(_) => SessionError::IOError,
            session::SessionError::SerdeJson(_) => SessionError::SessionCorruptData,
            session::SessionError::TooManySessions => SessionError::SessionTooMany,
        },
        CapiError::Utf8(_) => SessionError::Utf8Error,
        CapiError::FromBytesWithNul(_) => SessionError::StringConvertError,
    }
}

static ERROR_MESSAGES: &'static [&'static str] = &[
    "success\0",
    "IO error\0",
    "session with the given name already exists\0",
    "session data file is corrupt\0",
    "session buffer is too small\0",
    "too many sessions\0",
    "error parsing range\0",
    "unknown level\0",
    "unknown strategy\0",
    "utf-8 encoding error\0",
    "unknown book\0",
    "error converting null-terminated string\0",
];

#[no_mangle]
pub unsafe fn session_create(sess: *const imp::Session) -> c_int {
    match imp::session_create(&*sess) {
        Ok(()) => SessionError::OK as c_int,
        Err(ref e) => map_error_to_code(e) as c_int,
    }
}

mod imp {
    use super::*;
    use std::ffi::CStr;

    #[repr(C)]
    pub struct Session {
        pub name: [u8; 64],
        pub range: [Location; 2],
        pub level: u8,
        pub strategy: u8,
    }

    #[repr(C)]
    pub struct Location {
        pub translation: [u8; 8],
        pub book: [u8; 8],
        pub chapter: u16,
        pub sentence: u16,
        pub verse: u16,
    }

    impl Location {
        pub fn to_library_location(&self) -> Result<location::Location> {
            let translation = CStr::from_bytes_with_nul(&self.translation)?.to_str()?;
            let book = CStr::from_bytes_with_nul(&self.book)?.to_str()?;
            let book = Book::from_short_name(book)?;
            let chapter = self.chapter;
            let sentence = self.sentence;
            let verse = self.verse;
            Ok(location::Location {
                translation: translation.into(),
                book,
                chapter,
                sentence,
                verse,
            })
        }
    }

    pub fn session_create(sess: &Session) -> Result<()> {
        let name = str::from_utf8(&sess.name)?;
        let mut s = session::Session::named(&name);
        s.range = Range::default();
        s.range.start = sess.range[0].to_library_location()?;
        s.range.end = sess.range[1].to_library_location()?;
        s.level = sess.level.into();
        s.strategy = sess.strategy.into();
        s.write()?;
        Ok(())
    }
}

/// Frees the session from the heap.
#[no_mangle]
pub unsafe fn session_destroy(session: *mut Session) {
    Box::from_raw(session);
}

/// Writes the session to disk and deletes it.
#[no_mangle]
pub unsafe fn session_write(session: *mut Session) -> c_int {
    let session = Box::from_raw(session);
    if session.write().is_ok() {
        SessionError::OK as c_int
    } else {
        SessionError::IOError as c_int
    }
}

/// Deletes the session from disk.
#[no_mangle]
pub unsafe fn session_delete(session: *mut Session) -> c_int {
    let session = Box::from_raw(session);
    if session.delete().is_err() {
        SessionError::IOError as c_int
    } else {
        0
    }
}

#[no_mangle]
pub unsafe fn session_set_range(
    session: *mut Session,
    start: *const imp::Location,
    end: *const imp::Location,
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
    let book = if let Ok(book) = Book::from_short_name(book) {
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
    let book = if let Ok(book) = Book::from_short_name(book) {
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
