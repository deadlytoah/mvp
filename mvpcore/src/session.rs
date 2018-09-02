use dirs;
use level::Level;
use range::Range;
use serde_json;
use std::fmt::{self, Display, Formatter};
use std::fs::{self, OpenOptions};
use std::io::{BufReader, BufWriter, ErrorKind};
use std::path::PathBuf;
use strategy::Strategy;

const APP_DIR: &str = "mvp-speedtype";
const SESSIONS_FILE: &str = "sessions.json";
const MAX_SESSIONS: usize = 20;

type Result<T> = ::std::result::Result<T, SessionError>;

#[derive(Debug)]
pub enum SessionError {
    Io(::std::io::Error),
    SerdeJson(serde_json::Error),
    TooManySessions,
    SessionExists,
}

impl ::std::error::Error for SessionError {
    fn description(&self) -> &str {
        match *self {
            SessionError::Io(ref e) => e.description(),
            SessionError::SerdeJson(ref e) => e.description(),
            SessionError::TooManySessions => "too many sessions",
            SessionError::SessionExists => "session exists",
        }
    }

    fn cause(&self) -> Option<&::std::error::Error> {
        match *self {
            SessionError::Io(ref e) => Some(e),
            SessionError::SerdeJson(ref e) => Some(e),
            SessionError::TooManySessions => None,
            SessionError::SessionExists => None,
        }
    }
}

impl Display for SessionError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match *self {
            SessionError::Io(ref e) => write!(f, "IO error: {}", e),
            SessionError::SerdeJson(ref e) => write!(f, "serde_json error: {}", e),
            SessionError::TooManySessions => write!(f, "maximum number of sessions reached"),
            SessionError::SessionExists => write!(f, "session exists"),
        }
    }
}

impl From<::std::io::Error> for SessionError {
    fn from(err: ::std::io::Error) -> SessionError {
        SessionError::Io(err)
    }
}

impl From<serde_json::Error> for SessionError {
    fn from(err: serde_json::Error) -> SessionError {
        SessionError::SerdeJson(err)
    }
}

#[derive(Serialize, Deserialize)]
pub struct Session {
    pub name: String,
    pub range: Range,
    pub level: Level,
    pub strategy: Strategy,
}

impl Session {
    pub fn named(name: &str) -> Session {
        let mut session = Self::default();
        session.name = name.to_owned();
        session
    }

    pub fn load_all_sessions() -> Result<Vec<Session>> {
        let mut path = Session::sessions_dir();
        path.push(SESSIONS_FILE);

        match OpenOptions::new().read(true).open(&path) {
            Ok(file) => {
                let reader = BufReader::new(file);
                serde_json::from_reader(reader).map_err(|e| e.into())
            }
            Err(ref e) if e.kind() == ErrorKind::NotFound => Ok(vec![]),
            Err(e) => Err(e.into()),
        }
    }

    pub fn store_all_sessions(sessions: &[Session]) -> Result<()> {
        let mut path = Session::sessions_dir();
        if !path.exists() {
            fs::create_dir(&path)?;
        }
        path.push(SESSIONS_FILE);

        let writer = BufWriter::new(
            OpenOptions::new()
                .create(true)
                .truncate(true)
                .write(true)
                .open(&path)?,
        );
        serde_json::to_writer_pretty(writer, sessions)?;
        Ok(())
    }

    pub fn write(self) -> Result<()> {
        let mut session_seq = Session::load_all_sessions()?;
        if session_seq.len() > MAX_SESSIONS {
            Err(SessionError::TooManySessions)
        } else if session_seq.iter().any(|session| session.name == self.name) {
            Err(SessionError::SessionExists)
        } else {
            session_seq.push(self);
            Session::store_all_sessions(&session_seq)?;
            Ok(())
        }
    }

    pub fn delete(self) -> Result<()> {
        let mut session_seq = Session::load_all_sessions()?;
        session_seq.retain(|session| session.name != self.name);
        Session::store_all_sessions(&session_seq)?;
        Ok(())
    }

    fn sessions_dir() -> PathBuf {
        let mut path = dirs::data_dir().expect("data directory");
        path.push(APP_DIR);
        path
    }
}

impl Default for Session {
    fn default() -> Self {
        Session {
            name: Default::default(),
            range: Default::default(),
            level: Level::Level1,
            strategy: Strategy::Simple,
        }
    }
}
