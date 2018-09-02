use book::{Book, BookError};
use libc::*;
use location;
use range::Range;
use session;
use std::ffi;
use std::fmt::{self, Display, Formatter};
use std::slice;
use std::str;

type Result<T> = ::std::result::Result<T, CapiError>;

#[derive(Debug)]
pub enum CapiError {
    Book(BookError),
    Session(session::SessionError),
    Utf8(str::Utf8Error),
    Nul(ffi::NulError),
    BufferTooSmall,
}

impl ::std::error::Error for CapiError {
    fn description(&self) -> &str {
        match *self {
            CapiError::Book(ref e) => e.description(),
            CapiError::Session(ref e) => e.description(),
            CapiError::Utf8(ref e) => e.description(),
            CapiError::Nul(ref e) => e.description(),
            CapiError::BufferTooSmall => "buffer is too small",
        }
    }

    fn cause(&self) -> Option<&::std::error::Error> {
        match *self {
            CapiError::Book(ref e) => Some(e),
            CapiError::Session(ref e) => Some(e),
            CapiError::Utf8(ref e) => Some(e),
            CapiError::Nul(ref e) => Some(e),
            CapiError::BufferTooSmall => None,
        }
    }
}

impl Display for CapiError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match *self {
            CapiError::Book(ref e) => write!(f, "book error: {}", e),
            CapiError::Session(ref e) => write!(f, "session error: {}", e),
            CapiError::Utf8(ref e) => write!(f, "utf8 error: {}", e),
            CapiError::Nul(ref e) => write!(f, "nul character found in string: {}", e),
            CapiError::BufferTooSmall => write!(f, "buffer is too small"),
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

impl From<ffi::NulError> for CapiError {
    fn from(err: ffi::NulError) -> CapiError {
        CapiError::Nul(err)
    }
}

#[repr(C)]
pub enum SessionError {
    OK,
    IOError,
    SessionExists,
    SessionDataCorrupt,
    SessionBufferTooSmall,
    SessionTooMany,
    RangeParseError,
    LevelUnknown,
    StrategyUnknown,
    Utf8Error,
    BookUnknown,
    NulError,
}

fn map_error_to_code(error: &CapiError) -> SessionError {
    match *error {
        CapiError::Book(ref e) => match *e {
            BookError::UnknownBook { .. } => SessionError::BookUnknown,
        },
        CapiError::Session(ref e) => match *e {
            session::SessionError::Io(_) => SessionError::IOError,
            session::SessionError::SerdeJson(_) => SessionError::SessionDataCorrupt,
            session::SessionError::TooManySessions => SessionError::SessionTooMany,
            session::SessionError::SessionExists => SessionError::SessionExists,
        },
        CapiError::Utf8(_) => SessionError::Utf8Error,
        CapiError::Nul(_) => SessionError::NulError,
        CapiError::BufferTooSmall => SessionError::SessionBufferTooSmall,
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
    "unexpected null character found in string\0",
];

#[no_mangle]
pub unsafe fn session_create(sess: *const imp::Session) -> c_int {
    match imp::session_create(&*sess) {
        Ok(()) => SessionError::OK as c_int,
        Err(ref e) => map_error_to_code(e) as c_int,
    }
}

/// Returns the persisted sessions from disk.
///
/// Caller is required to allocate enough memory and pass the address
/// to the buffer in buf and the object count in *len.  Then the
/// address is populated with the sessions and the actual number of
/// sessions is recorded in *len.
///
/// buf and len must point to accessible memory addresses.
///
/// Each session is stored as per imp::Session data structure.
///
/// If buf is not large enough, returns SessionBufferTooSmall.  If
/// there is an error loading the sessions, returns
/// SessionDataCorrupt.  Otherwise returns OK and buf is filled with
/// sessions.
#[no_mangle]
pub unsafe fn session_list_sessions(buf: *mut imp::Session, len: *mut size_t) -> c_int {
    let size = *len;
    let bufslice = slice::from_raw_parts_mut(buf as *mut imp::Session, size);

    match imp::session_list_sessions(bufslice) {
        Ok(count) => {
            *len = count;
            SessionError::OK as c_int
        }
        Err(e) => map_error_to_code(&e) as c_int,
    }
}

/// Deletes the session from disk.
#[no_mangle]
pub unsafe fn session_delete(session: *mut imp::Session) -> c_int {
    match imp::session_delete(&*session) {
        Ok(_) => SessionError::OK as c_int,
        Err(e) => map_error_to_code(&e) as c_int,
    }
}

#[no_mangle]
pub fn session_get_message(error_code: c_int) -> *const c_char {
    ERROR_MESSAGES[error_code as usize].as_ptr() as *const c_char
}

mod imp {
    use super::*;
    use book;
    use std::ffi::{CStr, CString};

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
            let translation = unsafe { CStr::from_ptr(self.translation.as_ptr() as *const i8) };
            let translation = translation.to_str()?;
            let book = unsafe { CStr::from_ptr(self.book.as_ptr() as *const i8) };
            let book = book.to_str()?;
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

        pub fn copy_from_library_location(&mut self, loc: &location::Location) -> Result<()> {
            self.chapter = loc.chapter;
            self.sentence = loc.sentence;
            self.verse = loc.verse;

            let translation = CString::new(loc.translation.clone())?;
            let translation = translation.as_bytes_with_nul();
            self.translation[..translation.len()].copy_from_slice(translation);

            let book = book::get_short_name(loc.book);
            let book = CString::new(book)?;
            let book = book.as_bytes_with_nul();
            self.book[..book.len()].copy_from_slice(book);

            Ok(())
        }
    }

    pub fn session_create(sess: &Session) -> Result<()> {
        let name = unsafe { CStr::from_ptr(sess.name.as_ptr() as *const i8) };
        let name = name.to_str()?;
        let mut s = session::Session::named(&name);
        s.range = Range::default();
        s.range.start = sess.range[0].to_library_location()?;
        s.range.end = sess.range[1].to_library_location()?;
        s.level = sess.level.into();
        s.strategy = sess.strategy.into();
        s.write()?;
        Ok(())
    }

    /// Loads all sessions persisted on disk.
    pub fn session_list_sessions(seq: &mut [Session]) -> Result<usize> {
        let sessions = session::Session::load_all_sessions()?;
        let session_count = sessions.len();

        if session_count > seq.len() {
            Err(CapiError::BufferTooSmall)
        } else {
            for (i, session) in sessions.into_iter().enumerate() {
                let buf = &mut seq[i];

                let name = CString::new(session.name)?;
                let name = name.as_bytes_with_nul();
                buf.name[..name.len()].copy_from_slice(name);

                buf.range[0].copy_from_library_location(&session.range.start)?;
                buf.range[1].copy_from_library_location(&session.range.end)?;

                buf.level = session.level as u8;
                buf.strategy = session.strategy as u8;
            }

            Ok(session_count)
        }
    }

    /// Deletes the session with the give name from disk.
    pub fn session_delete(session: &Session) -> Result<()> {
        let name = unsafe { CStr::from_ptr(session.name.as_ptr() as *const i8) };
        let name = name.to_str()?;
        let session = session::Session::named(name);
        session.delete()?;
        Ok(())
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use std::ffi::CStr;

    #[test]
    fn test_session_list_sessions() {
        let res = create_test_session();
        assert!(res == SessionError::OK as c_int || res == SessionError::SessionExists as c_int);

        let mut buf: [imp::Session; 20] = unsafe { ::std::mem::zeroed() };
        let mut len: usize = 20;
        {
            let bufref = &mut buf;
            let ret = unsafe { session_list_sessions(bufref.as_mut_ptr(), &mut len) };
            assert_eq!(ret, 0);
        }
        assert!(len > 0);

        let list = &buf[..len];
        let found = list.iter().any(|session| {
            let name = unsafe { CStr::from_ptr(session.name.as_ptr() as *const i8) };
            let name = name.to_str().expect("to_str");
            name == "test"
        });
        assert!(found);
    }

    #[test]
    fn test_session_create_existing() {
        let res = create_test_session();
        assert!(res == SessionError::OK as c_int || res == SessionError::SessionExists as c_int);

        // Try creating the same session again.
        let res = create_test_session();
        assert_eq!(res, SessionError::SessionExists as c_int);
    }

    fn create_test_session() -> c_int {
        let start = imp::Location {
            translation: [b'E', b'S', b'V', 0, 0, 0, 0, 0],
            book: [b'P', b'h', b'i', b'l', 0, 0, 0, 0],
            chapter: 1,
            sentence: 0,
            verse: 1,
        };
        let end = imp::Location {
            translation: [b'E', b'S', b'V', 0, 0, 0, 0, 0],
            book: [b'P', b'h', b'i', b'l', 0, 0, 0, 0],
            chapter: 2,
            sentence: 0,
            verse: 1,
        };

        let mut session = imp::Session {
            name: unsafe { ::std::mem::zeroed() },
            range: [start, end],
            level: 0,
            strategy: 0,
        };

        session.name[0..4].copy_from_slice(&[b't', b'e', b's', b't']);

        unsafe { session_create(&session) }
    }
}
