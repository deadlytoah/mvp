class Address:
    """Addresses a sentence in the flashcard"""

    def __init__(self, sentences, lookup, addr_tuple):
        self.sentences = sentences
        self.lookup = lookup
        self.book, self.chapter, self.sentence = addr_tuple

    def __repr__(self):
        return '{0} {1}#{2}'.format(self.book, self.chapter, self.sentence)

    def move_up(self):
        target = self.sentence - 1
        if target < 0:
            pass
        else:
            self.sentence = target

    def move_down(self):
        target = self.sentence + 1
        if target >= len(self.sentences):
            pass
        else:
            self.sentence = target
