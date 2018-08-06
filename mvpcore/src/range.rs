use book::Book;
use location::Location;

#[derive(Serialize, Deserialize)]
pub struct Range {
    pub start: Location,
    pub end: Location,
}

impl Default for Range {
    /// Return the range of scripture that covers the beginning to the
    /// end in the ESV translation.
    fn default() -> Self {
        Range {
            start: Location {
                translation: "ESV".to_owned(),
                book: Book::Genesis,
                chapter: 1,
                sentence: 0,
                verse: 1,
            },
            end: Location {
                translation: "ESV".to_owned(),
                book: Book::Revelation,
                chapter: 22,
                sentence: 29,
                verse: 21,
            },
        }
    }
}
