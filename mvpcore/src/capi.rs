use libc::*;
use model::speedtype::{compat, strong};
use model::strong::BookError;
use model::strong::Range;
use sdb;
use std::ffi;
use std::fmt::{self, Display, Formatter};
use std::slice;
use std::str;

pub type Result<T> = ::std::result::Result<T, CapiError>;

#[derive(Debug)]
pub enum CapiError {
    Book(BookError),
    Session(strong::SessionError),
    Utf8(str::Utf8Error),
    Nul(ffi::NulError),
    Sdb(sdb::Error),
    Io(::std::io::Error),
    HttpRequest(::reqwest::Error),
    Regex(::regex::Error),
    Fetch(::verse::FetchError),
    BufferTooSmall,
}

impl ::std::error::Error for CapiError {
    fn description(&self) -> &str {
        match *self {
            CapiError::Book(ref e) => e.description(),
            CapiError::Session(ref e) => e.description(),
            CapiError::Utf8(ref e) => e.description(),
            CapiError::Nul(ref e) => e.description(),
            CapiError::Sdb(ref e) => e.description(),
            CapiError::Io(ref e) => e.description(),
            CapiError::HttpRequest(ref e) => e.description(),
            CapiError::Regex(ref e) => e.description(),
            CapiError::Fetch(ref e) => e.description(),
            CapiError::BufferTooSmall => "buffer is too small",
        }
    }

    fn cause(&self) -> Option<&::std::error::Error> {
        match *self {
            CapiError::Book(ref e) => Some(e),
            CapiError::Session(ref e) => Some(e),
            CapiError::Utf8(ref e) => Some(e),
            CapiError::Nul(ref e) => Some(e),
            CapiError::Sdb(ref e) => Some(e),
            CapiError::Io(ref e) => Some(e),
            CapiError::HttpRequest(ref e) => Some(e),
            CapiError::Regex(ref e) => Some(e),
            CapiError::Fetch(ref e) => Some(e),
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
            CapiError::Sdb(ref e) => write!(f, "error in database: {}", e),
            CapiError::Io(ref e) => write!(f, "IO error: {}", e),
            CapiError::HttpRequest(ref e) => write!(f, "error making an HTTP request: {}", e),
            CapiError::Regex(ref e) => write!(f, "Regex error: {}", e),
            CapiError::Fetch(ref e) => write!(f, "error fetching verse: {}", e),
            CapiError::BufferTooSmall => write!(f, "buffer is too small"),
        }
    }
}

impl From<BookError> for CapiError {
    fn from(err: BookError) -> CapiError {
        CapiError::Book(err)
    }
}

impl From<strong::SessionError> for CapiError {
    fn from(err: strong::SessionError) -> CapiError {
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

impl From<sdb::Error> for CapiError {
    fn from(err: sdb::Error) -> CapiError {
        CapiError::Sdb(err)
    }
}

impl From<::std::io::Error> for CapiError {
    fn from(err: ::std::io::Error) -> CapiError {
        CapiError::Io(err)
    }
}

impl From<::reqwest::Error> for CapiError {
    fn from(err: ::reqwest::Error) -> CapiError {
        CapiError::HttpRequest(err)
    }
}

impl From<::regex::Error> for CapiError {
    fn from(err: ::regex::Error) -> CapiError {
        CapiError::Regex(err)
    }
}

impl From<::verse::FetchError> for CapiError {
    fn from(err: ::verse::FetchError) -> CapiError {
        CapiError::Fetch(err)
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
    SdbError,
    HttpRequestError,
    RegexError,
    FetchError,
}

pub fn map_error_to_code(error: &CapiError) -> SessionError {
    match *error {
        CapiError::Book(ref e) => match *e {
            BookError::UnknownBook { .. } => SessionError::BookUnknown,
        },
        CapiError::Session(ref e) => match *e {
            strong::SessionError::Io(_) => SessionError::IOError,
            strong::SessionError::SerdeJson(_) => SessionError::SessionDataCorrupt,
            strong::SessionError::TooManySessions => SessionError::SessionTooMany,
            strong::SessionError::SessionExists => SessionError::SessionExists,
        },
        CapiError::Utf8(_) => SessionError::Utf8Error,
        CapiError::Nul(_) => SessionError::NulError,
        CapiError::BufferTooSmall => SessionError::SessionBufferTooSmall,
        CapiError::Sdb(_) => SessionError::SdbError,
        CapiError::Io(_) => SessionError::IOError,
        CapiError::HttpRequest(_) => SessionError::HttpRequestError,
        CapiError::Regex(_) => SessionError::RegexError,
        CapiError::Fetch(_) => SessionError::FetchError,
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
    "error in database\0",
    "error making an HTTP request\0",
    "regex error\0",
    "error fetching verses\0",
];

#[no_mangle]
pub unsafe fn session_create(sess: *const compat::Session) -> c_int {
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
/// Each session is stored as per model::speedtype::compat::Session
/// data structure.
///
/// If buf is not large enough, returns SessionBufferTooSmall.  If
/// there is an error loading the sessions, returns
/// SessionDataCorrupt.  Otherwise returns OK and buf is filled with
/// sessions.
#[no_mangle]
pub unsafe fn session_list_sessions(buf: *mut compat::Session, len: *mut size_t) -> c_int {
    let size = *len;
    let bufslice = slice::from_raw_parts_mut(buf as *mut compat::Session, size);

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
pub unsafe fn session_delete(session: *mut compat::Session) -> c_int {
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
    use model::speedtype::compat::Session;
    use std::ffi::{CStr, CString};

    pub fn session_create(sess: &Session) -> Result<()> {
        let name = unsafe { CStr::from_ptr(sess.name.as_ptr() as *const i8) };
        let name = name.to_str()?;
        let mut s = strong::Session::named(&name);
        s.range = Range::default();
        s.range.start = sess.range[0].to_strong_typed()?;
        s.range.end = sess.range[1].to_strong_typed()?;
        s.level = sess.level.into();
        s.strategy = sess.strategy.into();
        s.write()?;
        Ok(())
    }

    /// Loads all sessions persisted on disk.
    pub fn session_list_sessions(seq: &mut [Session]) -> Result<usize> {
        let sessions = strong::Session::load_all_sessions()?;
        let session_count = sessions.len();

        if session_count > seq.len() {
            Err(CapiError::BufferTooSmall)
        } else {
            for (i, session) in sessions.into_iter().enumerate() {
                let buf = &mut seq[i];

                let name = CString::new(session.name)?;
                let name = name.as_bytes_with_nul();
                buf.name[..name.len()].copy_from_slice(name);

                buf.range[0].copy_from_strong_typed(&session.range.start)?;
                buf.range[1].copy_from_strong_typed(&session.range.end)?;

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
        let session = strong::Session::named(name);
        session.delete()?;
        Ok(())
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use model;
    use std::ffi::CStr;

    #[test]
    fn test_session_list_sessions() {
        let res = create_test_session().0;
        assert!(res == SessionError::OK as c_int || res == SessionError::SessionExists as c_int);

        let mut buf: [model::speedtype::compat::Session; 20] = unsafe { ::std::mem::zeroed() };
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
        let res = create_test_session().0;
        assert!(res == SessionError::OK as c_int || res == SessionError::SessionExists as c_int);

        // Try creating the same session again.
        let res = create_test_session().0;
        assert_eq!(res, SessionError::SessionExists as c_int);
    }

    #[test]
    fn test_session_delete() {
        let (res, mut session) = create_test_session();
        assert!(res == SessionError::OK as c_int || res == SessionError::SessionExists as c_int);

        let res = unsafe { session_delete(&mut session) };
        assert_eq!(res, 0);

        let mut buf: [model::speedtype::compat::Session; 20] = unsafe { ::std::mem::zeroed() };
        let mut len: usize = 20;
        {
            let bufref = &mut buf;
            let ret = unsafe { session_list_sessions(bufref.as_mut_ptr(), &mut len) };
            assert_eq!(ret, 0);
        }

        let list = &buf[..len];
        let none = list.iter().all(|session| {
            let name = unsafe { CStr::from_ptr(session.name.as_ptr() as *const i8) };
            let name = name.to_str().expect("to_str");
            name != "test"
        });
        assert!(none);
    }

    fn create_test_session() -> (c_int, model::speedtype::compat::Session) {
        let start = model::compat::Location {
            translation: [b'E', b'S', b'V', 0, 0, 0, 0, 0],
            book: [b'P', b'h', b'i', b'l', 0, 0, 0, 0],
            chapter: 1,
            sentence: 0,
            verse: 1,
        };
        let end = model::compat::Location {
            translation: [b'E', b'S', b'V', 0, 0, 0, 0, 0],
            book: [b'P', b'h', b'i', b'l', 0, 0, 0, 0],
            chapter: 2,
            sentence: 0,
            verse: 1,
        };

        let mut session = model::speedtype::compat::Session {
            name: unsafe { ::std::mem::zeroed() },
            range: [start, end],
            level: 0,
            strategy: 0,
        };

        session.name[0..4].copy_from_slice(&[b't', b'e', b's', b't']);

        let res = unsafe { session_create(&session) };
        (res, session)
    }
}
