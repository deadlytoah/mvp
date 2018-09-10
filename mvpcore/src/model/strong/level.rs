#[allow(unused)]
const PUNCTUATIONS: &[char] = &['.', ',', ':', ';', '[', ']'];

#[derive(Serialize, Deserialize)]
pub enum Level {
    Level1,
    Level2,
    Level3,
    Level4,
    Level5,
}

impl From<u8> for Level {
    fn from(val: u8) -> Level {
        if val > 4 {
            panic!("value {} out of range for Level", val)
        } else {
            unsafe { ::std::mem::transmute(val) }
        }
    }
}

#[allow(unused)]
const PRONOUNS: &[&str] = &[
    "i",
    "we",
    "they",
    "she",
    "he",
    "you",
    "my",
    "mine",
    "our",
    "ours",
    "their",
    "theirs",
    "her",
    "hers",
    "his",
    "hers",
    "your",
    "yours",
    "me",
    "us",
    "them",
    "him",
    "while",
    "when",
    "where",
    "how",
    "who",
    "whom",
    "why",
    "whenever",
    "wherever",
    "however",
    "whoever",
    "whomever",
    "whosoever",
];

#[allow(unused)]
const ARTICLES: &[&str] = &[
    "to",
    "for",
    "in",
    "on",
    "at",
    "toward",
    "towards",
    "afterward",
    "afterwards",
    "over",
    "under",
    "across",
    "beyond",
    "before",
    "after",
    "unto",
    "onto",
    "inside",
    "through",
    "throughout",
    "therefore",
    "moreover",
    "if",
    "but",
    "and",
    "or",
    "hence",
    "thus",
];

#[allow(unused)]
#[derive(Clone)]
#[repr(C)]
enum Kind {
    Pronoun,
    Article,
}

#[derive(Clone)]
#[repr(C)]
struct Word {
    pub value: String,
    pub hidden: bool,
    pub kind: Kind,
}

#[allow(unused)]
#[repr(C)]
struct Permutation {
    pub words: Vec<Word>,

    /// How dispersed are the hidden words?
    pub dispersion: f64,

    /// How many pronouns are hidden?
    pub pronouns: f64,

    /// How many articles are hidden?
    pub articles: f64,
}
