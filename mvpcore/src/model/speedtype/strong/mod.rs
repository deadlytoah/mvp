pub mod character;
mod level;
pub mod word;

pub use self::character::*;
pub use self::level::*;
pub use self::word::*;

use model::speedtype::compat;

#[derive(Debug, Default)]
pub struct Sentence(pub Vec<WordId>);

impl From<compat::Sentence> for Sentence {
    fn from(from: compat::Sentence) -> Self {
        Sentence(from.0.into())
    }
}

/// Represents the internal state of the SpeedType view.
///
/// This represents the internal and external elements of the
/// SpeedType view.  It includes letters, words and sentences and
/// their individual states.  It also includes the state of the caret.
///
/// It is rendered into the render structure.  The render structure is
/// platform dependent.  It contains primitives that are used to paint
/// or update the screen.
///
/// It is a comprehensive data structure useful for saving and
/// restoring session.
#[derive(Debug, Default)]
pub struct State {
    /// sequential storage of characters to display and their
    /// states. This includes correct or incorrect entries and which
    /// word each character belongs to.
    pub buffer: Vec<Character>,

    /// list of words and their states.
    pub words: Vec<Word>,

    /// list of indices to words that belong to each sentence.
    pub sentences: Vec<Sentence>,
}

impl From<compat::State> for State {
    fn from(from: compat::State) -> Self {
        let buffer: Vec<_> = from.buffer.into();
        let words: Vec<_> = from.words.into();
        let sentences: Vec<_> = from.sentences.into();

        Self {
            buffer: buffer.into_iter().map(From::from).collect(),
            words: words.into_iter().map(From::from).collect(),
            sentences: sentences.into_iter().map(From::from).collect(),
        }
    }
}

impl State {
    pub fn new() -> Self {
        Self::default()
    }
}
