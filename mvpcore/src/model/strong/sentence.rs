use libc::{self, c_char};
use model::compat;
use std::ffi::CStr;
use std::mem::replace;
use std::slice;

const TERMINATING_PUNCTS: &str = ".:;?!";
const NON_TERMINATING_PUNCTS: &str = r#"()[]<>"'"#;

#[derive(Debug)]
enum PunctuationKind {
    Terminating {
        // Wait, There is More
        //
        // Non-terminating punctuations that follow a terminating one
        // belong in the sentence it is terminating.
        precedes_punctuation: bool,
    },
    NonTerminating {
        // End of Sentence
        //
        // Preceding whitespace means we will stop looking (expecting)
        // another punctuation after this.  Thus we conclude this
        // sentence.
        precedes_whitespace: bool,

        // Indicates this is the last character in the string.
        end_of_string: bool,
    },
}

#[derive(Debug)]
struct Punctuation {
    index: usize,
    punctuation: char, // for debugging
    kind: PunctuationKind,
}

impl Punctuation {
    fn is_terminating(&self) -> bool {
        if let PunctuationKind::Terminating { .. } = self.kind {
            true
        } else {
            false
        }
    }

    fn from_char(index: usize, ch: char, next_char: Option<char>) -> Option<Self> {
        if TERMINATING_PUNCTS.contains(ch) {
            Some(Punctuation {
                index,
                punctuation: ch,
                kind: PunctuationKind::Terminating {
                    precedes_punctuation: next_char.is_some()
                        && (TERMINATING_PUNCTS.contains(next_char.unwrap())
                            || NON_TERMINATING_PUNCTS.contains(next_char.unwrap())),
                },
            })
        } else if NON_TERMINATING_PUNCTS.contains(ch) {
            Some(Punctuation {
                index,
                punctuation: ch,
                kind: PunctuationKind::NonTerminating {
                    precedes_whitespace: next_char.is_some() && next_char.unwrap().is_whitespace(),
                    end_of_string: next_char.is_none(),
                },
            })
        } else {
            None
        }
    }

    fn from_str(text: &str) -> Vec<Self> {
        text.chars()
            .enumerate()
            .map(|(i, ch)| Punctuation::from_char(i, ch, text.chars().nth(i + 1)))
            .filter(Option::is_some)
            .map(Option::unwrap)
            .collect()
    }
}

#[derive(Default)]
pub struct Source {
    pub verse: usize,
    pub part_id: usize,
    pub is_whole: bool,
}

#[derive(Default)]
pub struct Sentence {
    pub text: String,
    pub sources: Vec<Source>,
}

/// Represents a part of a verse that are separated by sentence
/// terminating delimiters.
#[derive(Debug)]
struct Segment {
    id: usize,
    text: String,
    origin: usize,
    is_final: bool,
    is_whole: bool,
}

pub struct SentencesFromVerses {
    pub sentences: Vec<Sentence>,
    pub lookup: Vec<usize>,
}

impl Sentence {
    pub fn sentences_from_verses(verses: &[&str]) -> SentencesFromVerses {
        // step 1 split verses into a queue of partial or whole
        // verses.
        let indices = verses
            .iter()
            .map(|verse| Punctuation::from_str(verse))
            .map(|verse_puncts| {
                let mut indices = vec![];

                // Sequence of adjacent punctuations led by a
                // terminating one.
                let mut state = vec![];

                for punct in verse_puncts {
                    let mut output = None;

                    match punct.kind {
                        PunctuationKind::Terminating {
                            precedes_punctuation: true,
                        } => {
                            debug_assert!(state.is_empty());
                            state.push(punct);
                        }
                        PunctuationKind::Terminating {
                            precedes_punctuation: false,
                        } => {
                            debug_assert!(state.is_empty());
                            output = Some(punct.index);
                        }
                        PunctuationKind::NonTerminating {
                            precedes_whitespace: false,
                            end_of_string: false,
                        } => {
                            if !state.is_empty() {
                                debug_assert!(state[0].is_terminating());
                                state.push(punct);
                            }
                        }
                        PunctuationKind::NonTerminating { .. } => {
                            if !state.is_empty() {
                                debug_assert!(state[0].is_terminating());
                                for (i, p) in state.iter().rev().enumerate() {
                                    debug_assert_eq!(p.index, punct.index - (i + 1));
                                }
                                output = Some(punct.index);
                                state.clear();
                            }
                        }
                    }

                    if let Some(output) = output {
                        indices.push(output);
                    }
                }
                indices
            })
            .collect::<Vec<_>>();

        let queue = verses
            .iter()
            .enumerate()
            .map(|(i, text)| split_verse(i + 1, text, &indices[i]))
            .flatten();

        // step 2 process the queue to produce sentences and look up
        // table.
        let mut sentences = vec![];
        let mut lookup = vec![];
        let mut sentence_segments = vec![];
        let mut sentence: Option<Sentence> = None;
        for segment in queue {
            let mut sentence = sentence.take().unwrap_or_default();
            sentence_segments.push(segment.text);
            sentence.sources.push(Source {
                verse: segment.origin,
                part_id: segment.id,
                is_whole: segment.is_whole,
            });

            if lookup.len() < segment.origin {
                lookup.push(sentences.len());
            }

            if segment.is_final {
                sentence.text = replace(&mut sentence_segments, vec![]).join(" ");
                sentences.push(sentence);
            }
        }

        SentencesFromVerses { sentences, lookup }
    }
}

#[no_mangle]
pub unsafe fn sentences_from_verses(
    verses_ptr: *const *const c_char,
    verses_len: libc::size_t,
    sentences_ptr: *mut compat::Sentence,
    sentences_len: *mut libc::size_t,
) {
    let mut verses = vec![];
    for i in 0..verses_len {
        let text = *verses_ptr.add(i);
        let text = CStr::from_ptr(text);
        let text = text.to_str().expect("utf8 error");
        verses.push(text);
    }

    let sentences = Sentence::sentences_from_verses(&verses).sentences;
    let out_buffer = slice::from_raw_parts_mut(sentences_ptr, *sentences_len);
    *sentences_len = sentences.len();
    sentences
        .into_iter()
        .enumerate()
        .for_each(|(i, sentence)| out_buffer[i].copy_from(sentence));
}

/// Splits a verse into segments where sentences in the verse are
/// terminated.
fn split_verse(verse: usize, text: &str, indices: &[usize]) -> Vec<Segment> {
    let mut start = 0;

    // use of trim_start() is due to a whitespace that follows a
    // punctuation.
    let mut segments = indices
        .iter()
        .enumerate()
        .scan(&mut start, |start, (j, index)| {
            let value = Segment {
                id: j,
                text: text[**start..=*index].trim_start().into(),
                origin: verse,
                is_final: true,
                is_whole: false,
            };
            **start = index + 1;
            Some(value)
        })
        .collect::<Vec<_>>();

    if !text[start..].is_empty() {
        let segments_len = segments.len();
        segments.push(Segment {
            id: segments_len,
            text: text[start..].trim_start().into(),
            origin: verse,
            is_final: false,
            is_whole: false,
        });
    }

    if segments.len() == 1 {
        segments[0].is_whole = true;
    }

    segments
}

#[cfg(test)]
mod test {
    use super::Sentence;

    #[test]
    fn split_verse() {
        let text = "Mission: Impossible.";
        let indices = &[7, 19];
        let segments = super::split_verse(2, text, indices);
        assert_eq!(segments[0].text, "Mission:");
        assert_eq!(segments[1].text, "Impossible.");
    }

    #[test]
    fn non_terminating_punctuations() {
        // text from John 1:15-16 ESV
        let verses = &[
            "(John bore witness about him, and cried out, \"This was he of \
             whom I said, 'He who comes after me ranks before me, because \
             he was before me.'\")",
            "For from his fullness we have all received, grace upon grace.",
        ];
        let expected = &[
            "(John bore witness about him, and cried out, \"This was he of \
             whom I said, 'He who comes after me ranks before me, because \
             he was before me.'\")",
            "For from his fullness we have all received, grace upon grace.",
        ];

        for (i, sentence) in Sentence::sentences_from_verses(verses)
            .sentences
            .iter()
            .enumerate()
        {
            assert_eq!(sentence.text, expected[i]);
        }
    }
}
