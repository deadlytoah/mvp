use model::strong::book::Book;

#[derive(Serialize, Deserialize)]
pub struct Location {
    // code for the translation, which is uppercase letters, usually 3
    // to 4 letters long.
    pub translation: String,

    pub book: Book,

    // chapter number, starts with 1.
    pub chapter: u16,

    // the index of the sentence as appears in the chapter.
    pub sentence: u16,

    // this is a verse number that the sentence belongs to, and is
    // there for data transformation.  Starts with 1.
    pub verse: u16,
}
