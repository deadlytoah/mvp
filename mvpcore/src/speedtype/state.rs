use capi::Result;
use libc;
use model::character::Character;
use model::word::{Word, WordId};
use std::boxed::Box;
use std::ffi::CStr;

const WORD_DELIMITERS: &str = " .,:;?!";

/// Represents the internal state of the SpeedType view.
///
/// This represents the internal and external elements of the
/// SpeedType view.  It includes letters, words and sentences and
/// their individual states.  It also includes the state of the caret.
///
/// It is rendered into the render structure.  The render structure is
/// then used to paint or update the screen.
///
/// It is a comprehensive data structure useful for saving and
/// restoring session.
///
/// Right now it is designed to be opaque to frontend components.  The
/// render structure is what faces the frontends.
#[derive(Debug, Default)]
pub struct SpeedTypeState {
    buffer: Vec<Character>,
    words: Vec<Word>,
    sentences: Vec<Vec<WordId>>,
}

/// Allocates memory for a SpeedTypeState and initialises it.
pub unsafe fn speedtype_new(state: *mut *mut SpeedTypeState) -> libc::c_int {
    *state = Box::into_raw(Box::new(SpeedTypeState::default()));
    0
}

/// Frees memory for a SpeedTypeState and sets it to null.
pub unsafe fn speedtype_delete(state: *mut *mut SpeedTypeState) -> libc::c_int {
    Box::from_raw(*state);
    *state = ::std::ptr::null_mut();
    0
}

/// Processes the given line of text.
///
/// Produces character buffer and groups the words together.  The
/// character buffer is used to show, hide and colour the letters.
/// The list of words is used to show or hide words.
#[no_mangle()]
pub unsafe fn speedtype_process_line(
    state: *mut SpeedTypeState,
    line: *const libc::c_char,
) -> libc::c_int {
    let line = CStr::from_ptr(line);
    match imp::process_line(&mut *state, line) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("{:?}", e);
            1
        }
    }
}

mod imp {
    use super::*;

    pub fn process_line(state: &mut SpeedTypeState, line: &CStr) -> Result<()> {
        let base_char_id = state.buffer.len();
        let base_word_id = state.words.len();

        let line = line.to_str()?;

        let mut buf = vec![];
        let mut words = vec![];

        let mut make_word = Word::with_id(base_word_id);

        for ch in line.chars() {
            let maybe_letter = Character::with_id_and_char(base_char_id + buf.len(), ch);
            buf.push(maybe_letter);

            if WORD_DELIMITERS.contains(ch) {
                if !make_word.word.is_empty() {
                    words.push(make_word);
                    make_word = Word::with_id(base_word_id + words.len());
                }
            } else {
                let letter = buf.last_mut().expect("buf.last()");
                make_word.push(letter);
            }
        }

        // the last word in the line
        if !make_word.word.is_empty() {
            words.push(make_word);
        }

        // end of line
        let id = base_char_id + buf.len();
        buf.push(Character::with_id_and_char(id, '\n'));

        state
            .sentences
            .push(words.iter().map(|word| word.id).collect());
        state.buffer.append(&mut buf);
        state.words.append(&mut words);

        Ok(())
    }
}
