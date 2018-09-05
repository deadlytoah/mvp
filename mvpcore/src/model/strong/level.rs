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

static PRONOUNS: &[&str] = &[
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

static ARTICLES: &[&str] = &[
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

static punctuations: &[char] = &['.', ',', ':', ';', '[', ']'];

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
