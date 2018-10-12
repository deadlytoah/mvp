extern crate dirs;
extern crate libc;
extern crate petgraph;
extern crate rand;
extern crate regex;
extern crate reqwest;
#[cfg(feature = "cache_uses_sdb")]
extern crate sdb;
extern crate serde;
#[cfg(feature = "cache_uses_sqlite")]
extern crate sqlite3;
#[macro_use]
extern crate serde_derive;
extern crate serde_json;

mod capi;
mod layout;
mod model;
mod scraper;
mod speedtype;
mod verse;

pub use capi::*;
pub use layout::graph::*;
pub use model::speedtype::strong::speedtype_apply_level;
pub use model::strong::sentences_from_verses;
pub use speedtype::state::*;
pub use verse::*;
