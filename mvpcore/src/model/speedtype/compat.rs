use libc;
use model::compat;
use model::speedtype;
use model::speedtype::strong;
use std::ffi::CString;
use std::mem;
use std::ptr;

pub type CharacterId = libc::size_t;
pub type WordId = libc::size_t;

#[derive(Debug)]
#[repr(C)]
pub struct Buffer<T> {
    pub len: libc::size_t,
    pub ptr: *mut T,
}

impl<T> Default for Buffer<T> {
    fn default() -> Self {
        Buffer {
            len: 0,
            ptr: ptr::null_mut(),
        }
    }
}

impl<T> From<Vec<T>> for Buffer<T> {
    fn from(from: Vec<T>) -> Self {
        let mut slice = from.into_boxed_slice();
        let ptr = slice.as_mut_ptr();
        let len = slice.len();
        mem::forget(slice);
        Self { len, ptr }
    }
}

impl<T> Into<Vec<T>> for Buffer<T> {
    fn into(self) -> Vec<T> {
        unsafe { Vec::<T>::from_raw_parts(self.ptr, self.len, self.len) }
    }
}

impl From<String> for Buffer<libc::c_char> {
    fn from(from: String) -> Self {
        let mut bytes = from.into_bytes().into_boxed_slice();
        let len = bytes.len();
        let ptr = bytes.as_mut_ptr() as *mut libc::c_char;
        mem::forget(bytes);
        Self { len, ptr }
    }
}

impl Into<String> for Buffer<libc::c_char> {
    fn into(self) -> String {
        let len = self.len;
        let ptr = self.ptr as *mut u8;
        unsafe { String::from_raw_parts(ptr, len, len) }
    }
}

impl<T> Buffer<T> {
    pub fn into_vec(self) -> Vec<T> {
        self.into()
    }
}

#[derive(Debug)]
#[repr(C)]
pub struct Character {
    pub id: CharacterId,
    pub character: libc::uint32_t,
    pub whitespace: libc::boolean_t,
    pub newline: libc::boolean_t,
    pub has_word: libc::boolean_t,
    pub word: WordId,
    pub visible: libc::boolean_t,
    pub has_typed: libc::boolean_t,
    pub typed: libc::uint32_t,
    pub correct: libc::boolean_t,
    pub rendered: libc::boolean_t,
}

impl From<strong::Character> for Character {
    fn from(from: strong::Character) -> Self {
        let mut to = Self {
            id: from.id,
            character: from.character as libc::uint32_t,
            whitespace: from.whitespace as libc::boolean_t,
            newline: from.newline as libc::boolean_t,
            has_word: Default::default(),
            word: Default::default(),
            visible: from.visible as libc::boolean_t,
            has_typed: Default::default(),
            typed: Default::default(),
            correct: from.correct as libc::boolean_t,
            rendered: from.rendered as libc::boolean_t,
        };

        match from.word {
            Some(word) => {
                to.has_word = 1;
                to.word = word;
            }
            None => to.has_word = 0,
        }

        match from.typed {
            Some(typed) => {
                to.has_typed = 1;
                to.typed = typed as libc::uint32_t;
            }
            None => to.has_typed = 0,
        }

        to
    }
}

#[derive(Debug)]
#[repr(C)]
pub struct Word {
    pub id: WordId,
    pub word: *mut libc::c_char,
    pub visible: libc::boolean_t,
    pub touched: libc::boolean_t,
    pub behind: libc::boolean_t,
    pub characters: Buffer<CharacterId>,
}

impl From<strong::Word> for Word {
    fn from(from: strong::Word) -> Self {
        let word = CString::new(from.word).expect("string contains nul");
        // into_boxed_slice() removes excess capacity.
        let mut word = word.into_bytes_with_nul().into_boxed_slice();
        let word_ptr = word.as_mut_ptr() as *mut libc::c_char;
        mem::forget(word);

        Self {
            id: from.id,
            word: word_ptr,
            visible: from.visible as libc::boolean_t,
            touched: from.touched as libc::boolean_t,
            behind: from.behind as libc::boolean_t,
            characters: from.characters.into(),
        }
    }
}

#[derive(Debug, Default)]
pub struct Sentence(pub Buffer<WordId>);

impl From<strong::Sentence> for Sentence {
    fn from(from: strong::Sentence) -> Self {
        Sentence(from.0.into())
    }
}

#[derive(Debug, Default)]
pub struct State {
    pub buffer: Buffer<Character>,
    pub words: Buffer<Word>,
    pub sentences: Buffer<Sentence>,
}

impl From<strong::State> for State {
    fn from(from: strong::State) -> Self {
        let buffer: Vec<_> = from.buffer.into_iter().map(From::from).collect();
        let words: Vec<_> = from.words.into_iter().map(From::from).collect();
        let sentences: Vec<_> = from.sentences.into_iter().map(From::from).collect();

        Self {
            buffer: buffer.into(),
            words: words.into(),
            sentences: sentences.into(),
        }
    }
}

#[repr(C)]
pub struct Session {
    pub name: [u8; 32],
    pub range: [compat::Location; 2],
    pub level: u8,
    pub strategy: u8,

    pub has_state: libc::boolean_t,
    pub state: speedtype::compat::State,
}

impl From<strong::Session> for Session {
    fn from(from: strong::Session) -> Self {
        let mut session: Session = unsafe { mem::zeroed() };
        let name = CString::new(from.name).expect("string contains nul");
        let name = name.as_bytes_with_nul();
        session.name[..name.len()].copy_from_slice(name);

        session.range[0]
            .copy_from_strong_typed(&from.range.start)
            .expect("string contains nul");
        session.range[1]
            .copy_from_strong_typed(&from.range.end)
            .expect("string contains nul");

        session.level = from.level as u8;
        session.strategy = from.strategy as u8;

        if let Some(from_state) = from.state {
            session.has_state = 1;
            session.state = from_state.into();
        } else {
            session.has_state = 0;
        }

        session
    }
}
