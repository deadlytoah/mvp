use std::mem;

#[derive(Serialize, Deserialize)]
#[repr(C)]
pub enum Book {
    ///////////////////
    // Old Testament //
    ///////////////////
    Genesis,
    Exodus,
    Leviticus,
    Numbers,
    Deuteronomy,
    Joshua,
    Judges,
    Ruth,
    _1Samuel,
    _2Samuel,
    _1Kings,
    _2Kings,
    _1Chronicles,
    _2Chronicles,
    Ezra,
    Nehemiah,
    Esther,
    Job,
    Psalms,
    Proverbs,
    Ecclesiastes,
    SongOfSolomon,
    Isaiah,
    Jeremiah,
    Lamentations,
    Ezekiel,
    Daniel,

    Hosea,
    Joel,
    Amos,
    Obadiah,
    Jonah,
    Micah,
    Nahum,
    Habakkuk,
    Zephaniah,
    Haggai,
    Zechariah,
    Malachi,

    ///////////////////
    // New Testament //
    ///////////////////
    Matthew,
    Mark,
    Luke,
    John,
    Acts,
    Romans,
    _1Corinthians,
    _2Corinthians,
    Galatians,
    Ephesians,
    Philippians,
    Colossians,
    _1Thessalonians,
    _2Thessalonians,
    _1Timothy,
    _2Timothy,
    Titus,
    Philemon,
    Hebrews,
    James,
    _1Peter,
    _2Peter,
    _1John,
    _2John,
    _3John,
    Jude,
    Revelation,
}

static SHORT_NAMES: &'static [&'static str] = &[
    ///////////////////
    // Old Testament //
    ///////////////////
    "Gen", "Ex", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1 Sam", "2 Sam", "1 Kings",
    "2 Kings", "1 Chron", "2 Chron", "Ezra", "Neh", "Est", "Job", "Ps", "Prov", "Eccles", "Song",
    "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah",
    "Hab", "Zeph", "Hag", "Zech", "Mal",
    ///////////////////
    // New Testament //
    ///////////////////
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1 Cor", "2 Cor", "Gal", "Eph", "Phil", "Col",
    "1 Thess", "2 Thess", "1 Tim", "2 Tim", "Titus", "Philem", "Heb", "James", "1 Pet", "2 Pet",
    "1 John", "2 John", "3 John", "Jude", "Rev",
];

impl Book {
    pub fn from_short_name(short_name: &str) -> Option<Self> {
        SHORT_NAMES
            .iter()
            .position(|n| *n == short_name)
            .map(|pos| unsafe { mem::transmute(pos as u32) })
    }
}

#[allow(dead_code)]
pub fn get_short_name(book: Book) -> &'static str {
    SHORT_NAMES[book as usize]
}
