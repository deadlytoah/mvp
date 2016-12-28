class Key:
    def __init__(self, book, chapter, verse):
        self.book = book
        self.chapter = chapter
        self.verse = verse

    def from_str(keystr):
        spl = keystr.split(' ', 1)
        book = spl[0]
        if len(spl) > 1 and len(spl[1]) > 0:
            spl = spl[1].replace('v', ':').split(':', 1)
            chapter = spl[0]
            if len(spl) > 1 and len(spl[1]) > 0:
                verse = spl[1]
            else:
                verse = None
        else:
            chapter = None
            verse = None

        return Key(book, chapter, verse)

    def __repr__(self):
        return '{0} {1}:{2}'.format(self.book, self.chapter, self.verse)
