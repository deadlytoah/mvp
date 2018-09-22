use model::speedtype::{compat, strong};
#[allow(unused_imports)]
use rand::{thread_rng, Rng};

#[allow(unused)]
const PUNCTUATIONS: &[char] = &['.', ',', ':', ';', '[', ']'];

#[derive(Clone, Copy, Serialize, Deserialize)]
pub enum Level {
    Level1,
    Level2,
    Level3,
    Level4,
    Level5,
}

impl Level {
    pub fn hidden_words(self) -> f32 {
        match self {
            Level::Level1 => 0.0,
            Level::Level2 => 0.2,
            Level::Level3 => 0.5,
            Level::Level4 => 0.7,
            Level::Level5 => 1.0,
        }
    }
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

#[no_mangle]
pub unsafe fn speedtype_apply_level(state: *mut compat::State, level: u8) {
    let mut s: compat::State = ::std::mem::uninitialized();
    ::std::ptr::copy_nonoverlapping(state, &mut s, 1);
    let mut s: strong::State = s.into();
    let level = Level::from(level);

    imp::apply_level(&mut s, level);
    let s: compat::State = s.into();
    ::std::ptr::copy_nonoverlapping(&s, state, 1);
}

mod imp {
    use super::*;

    /// Applies the difficulty level.
    ///
    /// Sets the difficulty level and shows or hides some words as
    /// appropriate.
    pub fn apply_level(state: &mut strong::State, level: Level) {
        let mut buffer: Option<&mut [_]> = Some(&mut state.buffer);
        let mut words: Option<&mut [_]> = Some(&mut state.words);
        let sentences = &state.sentences;

        for sentence in sentences {
            // I know the words are listed in the order they appear in
            // sentences.  I will cheat a little based on this
            // knowledge.
            let inner_words = words.take().unwrap();
            let (sentence_words, rest) = inner_words.split_at_mut(sentence.0.len());
            words = Some(rest);

            debug_assert!(
                sentence_words
                    .iter()
                    .map(|word| word.id)
                    .all(|id| sentence.0.contains(&id))
            );

            // Do the same with buffer.  Note that some characters do
            // not belong to a word.
            let last_char = *sentence_words.last().unwrap().characters.last().unwrap();
            let inner_buffer = buffer.take().unwrap();
            let index = inner_buffer
                .iter()
                .position(|ch| ch.id == last_char)
                .unwrap_or_else(|| panic!("char id {} not found", last_char));
            let (word_chars, rest) = inner_buffer.split_at_mut(index + 1);
            buffer = Some(rest);

            {
                let present_in_any_word = |id| {
                    sentence_words
                        .iter()
                        .any(|word| word.characters.contains(&id))
                };
                debug_assert!(
                    word_chars
                        .iter()
                        .all(|ch| ch.word.is_none() || present_in_any_word(ch.id))
                );
            }

            apply_level_to_words(word_chars, level, sentence_words);
        }
    }

    /// Applies the difficulty level in the given words.
    ///
    /// Sets the difficulty level and shows or hides some words as
    /// appropriate.
    fn apply_level_to_words(
        buffer: &mut [strong::Character],
        level: Level,
        words: &mut [strong::Word],
    ) {
        let word_count = words.iter().filter(|word| !word.behind).count();
        if word_count > 0 {
            let hidden = words
                .iter()
                .filter(|word| !word.behind && !word.visible)
                .count();

            let rate = hidden as f32 / word_count as f32;
            let target = level.hidden_words();

            if rate < target {
                // maybe hide more words
                let mut count = 0;
                while (hidden + count) as f32 / word_count as f32 <= target {
                    count += 1;
                }
                // don't exceed the target
                count -= 1;

                if count > 0 {
                    hide_random_words(buffer, words, count);
                }
            } else if rate > target {
                // reveal some words
                let mut count = 0;
                while (hidden - count) as f32 / word_count as f32 > target {
                    count += 1;
                }

                if count > 0 {
                    reveal_random_words(buffer, words, count);
                }
            }
        }
    }

    /// Hides the given number, count, of words from words.
    fn hide_random_words(
        buffer: &mut [strong::Character],
        words: &mut [strong::Word],
        count: usize,
    ) {
        debug_assert!(words.len() >= count);

        // all shown words that are untouched
        let mut words: Vec<_> = words
            .iter_mut()
            .filter(|word| word.visible && !word.behind)
            .collect();
        let mut rand = thread_rng();
        for _ in 0..count {
            let pick = rand.gen_range(0, words.len());

            // Not hiding words that have been touched.  This means
            // the hidden word ratio may sometimes be a little wrong,
            // but we don't care about accuracy here.
            if !words[pick].touched {
                hide_word(buffer, &mut words[pick]);
            }

            words.remove(pick);
        }
    }

    /// Reveals the given number, count, of words from words.
    fn reveal_random_words(
        buffer: &mut [strong::Character],
        words: &mut [strong::Word],
        count: usize,
    ) {
        debug_assert!(words.len() >= count);

        // all hidden words that are untouched
        let mut words: Vec<_> = words
            .iter_mut()
            .filter(|word| !word.visible && !word.behind)
            .collect();
        let mut rand = thread_rng();
        for _ in 0..count {
            let pick = rand.gen_range(0, words.len());
            reveal_word(buffer, &mut words[pick]);
            words.remove(pick);
        }
    }

    /// Hides a specific word.
    fn hide_word(buffer: &mut [strong::Character], word: &mut strong::Word) {
        word.visible = false;
        for ch in buffer.iter_mut().filter(|ch| ch.word == Some(word.id)) {
            ch.visible = false;
            ch.rendered = false;
        }
    }

    ///Reveals a specific word.
    fn reveal_word(buffer: &mut [strong::Character], word: &mut strong::Word) {
        word.visible = true;
        for ch in buffer.iter_mut().filter(|ch| ch.word == Some(word.id)) {
            ch.visible = true;
            ch.rendered = false;
        }
    }
}
