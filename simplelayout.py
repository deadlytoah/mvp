"""Maximum width of each line in number of characters"""
DEFAULT_LINE_WIDTH = 35

class SimpleLayout:
    def __init__(self):
        self.line_width = DEFAULT_LINE_WIDTH

    def set_line_width(self, lw):
        self.line_width = lw

    def layout(self, text):
        retval = []
        while len(text) > 0:
            s = text
            while len(s) >= self.line_width:
                s, last_removed = self._remove_last_word(s)

            # a word is longer than self.line_width
            if len(s) == 0:
                s = last_removed

            retval.append(s)
            text = text[len(s):].lstrip()
        return retval

    def _remove_last_word(self, text):
        rindex = text.rfind(' ')
        if rindex < 0:
            return ('', text)
        else:
            return (text[:rindex], text[rindex + 1:])
