#[allow(unused)]
pub enum Pattern {
    /// Everything that is not escaped falls into Exact.
    Exact(String),

    /// Matches a string of nod-escaped characters.
    Any,

    /// Matches \count, representing the number of verses.
    Count,

    /// Matches parenthesized ('\(', '\)')list of Patterns.
    Parenthesized(Vec<Pattern>),

    /// Matches \#, the verse number.  Must appear within \( and \).
    VerseNum,

    /// Matches \text, the actual text of the verse.  Must appear and
    /// appear within \( and \).
    Text,
}

#[cfg(test)]
mod test {
    // To use against the blb.org multi verse retrieval tool.
    const TEST_PROGRAM: &str = r#"<div id="multiResults">[\_:\_-\# \_]\( \# \text\)</div>"#;

    #[test]
    fn test_parsing_program() {}
}
