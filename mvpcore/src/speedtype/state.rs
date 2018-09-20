use capi::Result;
use libc;
use model::speedtype::compat;
use model::speedtype::strong;
use std::boxed::Box;
use std::ffi::CStr;

const WORD_DELIMITERS: &str = " .,:;?!";

/// Allocates memory for a SpeedTypeState and initialises it.
#[no_mangle()]
pub unsafe fn speedtype_new() -> *mut compat::State {
    let state = strong::State::new();
    let state: Box<compat::State> = Box::new(state.into());
    Box::into_raw(state)
}

/// Frees memory for a SpeedTypeState and sets it to null.
#[no_mangle()]
pub unsafe fn speedtype_delete(state: *mut compat::State) {
    // Buffer's do not free the resources automatically, so they need
    // to be converted to Vec and then be dropped.
    let state = Box::from_raw(state);
    let _: strong::State = (*state).into();
}

/// Processes the given line of text.
///
/// Produces character buffer and groups the words together.  The
/// character buffer is used to show, hide and colour the letters.
/// The list of words is used to show or hide words.
#[no_mangle()]
pub unsafe fn speedtype_process_line(
    state: *mut compat::State,
    line: *const libc::c_char,
) -> libc::c_int {
    let line = CStr::from_ptr(line);
    let mut s: compat::State = ::std::mem::uninitialized();
    ::std::ptr::copy_nonoverlapping(state, &mut s, 1);
    let mut s: strong::State = s.into();
    match imp::process_line(&mut s, line) {
        Ok(()) => {
            let s: compat::State = s.into();
            ::std::ptr::copy_nonoverlapping(&s, state, 1);
            0
        }
        Err(e) => {
            eprintln!("{:?}", e);
            1
        }
    }
}

mod imp {
    use super::*;
    use model::speedtype::strong::State as SpeedTypeState;
    use model::speedtype::strong::{Character, Sentence, Word};

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
            .push(Sentence(words.iter().map(|word| word.id).collect()));
        state.buffer.append(&mut buf);
        state.words.append(&mut words);

        Ok(())
    }
}
