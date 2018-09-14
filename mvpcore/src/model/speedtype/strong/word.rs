use model::speedtype::compat;
use model::speedtype::strong::{Character, CharacterId};
use std::ffi::CStr;

pub type WordId = usize;

#[derive(Debug)]
pub struct Word {
    pub id: WordId,
    pub word: String,
    pub visible: bool,
    pub touched: bool,
    pub behind: bool,
    pub characters: Vec<CharacterId>,
}

impl From<compat::Word> for Word {
    fn from(from: compat::Word) -> Self {
        let word = unsafe { CStr::from_ptr(from.word) };
        let word = word.to_string_lossy();
        let word = word.to_string();

        Self {
            id: from.id,
            word,
            visible: from.visible != 0,
            touched: from.touched != 0,
            behind: from.behind != 0,
            characters: from.characters.into(),
        }
    }
}

impl Word {
    /// Creates a new word with the given ID.
    pub fn with_id(id: WordId) -> Self {
        Word {
            id,
            word: String::new(),
            visible: true,
            touched: false,
            behind: false,
            characters: Default::default(),
        }
    }

    /// Appends the given letter to the word, and updates the
    /// relationship.
    pub fn push(&mut self, character: &mut Character) {
        character.word = Some(self.id);
        self.characters.push(character.id);
        self.word.push(character.character);
    }

    /// Gets the last character in the word.  Panics if there are no
    /// characters that belong to this word.
    pub fn last_character(&self) -> usize {
        *self.characters.last().expect("last_character")
    }
}
