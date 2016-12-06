"""Maximum width of each line in number of characters"""
MAX_LINE_WIDTH = 35

class SimpleLayout:
    def layout(self, text):
        retval = []
        while len(text) > 0:
            s = text
            while len(s) >= MAX_LINE_WIDTH:
                s = self._remove_last_word(s)

            # assumption here is a word will never be longer than
            # MAX_LINE_WIDTH characters
            assert(len(s) > 0)

            retval.append(s)
            text = text[len(s):]
        return retval

    def _remove_last_word(self, text):
        rindex = text.rfind(' ')
        if rindex < 0:
            return ''
        else:
            return text[:rindex]
