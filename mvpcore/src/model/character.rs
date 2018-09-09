pub type CharacterId = usize;

#[derive(Debug)]
pub struct Character {
    pub id: CharacterId,
    pub character: char,
    pub whitespace: bool,
    pub word: Option<usize>,
    pub visible: bool,
    pub typed: Option<char>,
    pub correct: bool,
}

impl Character {
    /// Creates a new character with the given ID and character.
    pub fn with_id_and_char(id: CharacterId, character: char) -> Self {
        Character {
            id,
            character,
            whitespace: character == ' ' || character == '\n',
            word: None,
            visible: true,
            typed: None,
            correct: false,
        }
    }
}
