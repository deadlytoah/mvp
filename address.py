class Address:
    """Addresses a sentence in the flashcard"""

    def __init__(self, book, chapter, sentence):
        self.book = book
        self.chapter = chapter
        self.sentence = sentence

    def __repr__(self):
        return '{0} {1}#{2}'.format(self.book, self.chapter, self.sentence)
