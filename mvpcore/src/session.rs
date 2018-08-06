use failure::Error;
use level::Level;
use range::Range;
use serde_json;
use std::fs::File;
use std::io::{BufReader, BufWriter};
use strategy::Strategy;

const SESSIONS_FILE: &str = "sessions.json";
const MAX_SESSIONS: usize = 100;

#[derive(Debug, Fail)]
pub enum SessionError {
    #[fail(display = "maximum number of sessions reached")]
    TooManySessions,
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

    pub fn load_all_sessions() -> Result<Vec<Session>, Error> {
        let reader = BufReader::new(File::open(SESSIONS_FILE)?);
        Ok(serde_json::from_reader(reader)?)
    }

    pub fn store_all_sessions(sessions: &[Session]) -> Result<(), Error> {
        let writer = BufWriter::new(File::open(SESSIONS_FILE)?);
        serde_json::to_writer_pretty(writer, sessions)?;
        Ok(())
    }

    pub fn write(self) -> Result<(), Error> {
        let mut session_seq = Session::load_all_sessions()?;
        if session_seq.len() > MAX_SESSIONS {
            bail!(SessionError::TooManySessions);
        } else {
            session_seq.push(self);
            Session::store_all_sessions(&session_seq)?;
            Ok(())
        }
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
