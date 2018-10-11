use model::speedtype::compat;
use model::speedtype::strong::WordId;
use std::char;

pub type CharacterId = usize;

#[derive(Debug, Deserialize, Serialize)]
pub struct Character {
    pub id: CharacterId,
    pub character: char,
    pub whitespace: bool,
    pub newline: bool,
    pub word: Option<WordId>,
    pub visible: bool,
    pub typed: Option<char>,
    pub correct: bool,
    pub rendered: bool,
}

impl Character {
    /// Creates a new character with the given ID and character.
    pub fn with_id_and_char(id: CharacterId, character: char) -> Self {
        Character {
            id,
            character,
            whitespace: character == ' ' || character == '\n',
            newline: character == '\n',
            word: None,
            visible: true,
            typed: None,
            correct: false,
            rendered: false,
        }
    }
}

impl From<compat::Character> for Character {
    fn from(from: compat::Character) -> Self {
        Self {
            id: from.id,
            character: char::from_u32(from.character).expect("Character::character"),
            whitespace: from.whitespace != 0,
            newline: from.newline != 0,
            word: match from.has_word {
                0 => None,
                _ => Some(from.word),
            },
            visible: from.visible != 0,
            typed: match from.has_typed {
                0 => None,
                _ => Some(char::from_u32(from.typed).expect("Character::typed")),
            },
            correct: from.correct != 0,
            rendered: from.rendered != 0,
        }
    }
}
