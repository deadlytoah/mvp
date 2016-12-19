"""Use an algorithm based on graph to layout words in the flash
card"""
MAX_WORD_PER_LINE = 6

class GraphLayout:
    def layout(self, text):
        retval = []
        queue = _create_word_queue(text)
        line = []

        for word in queue:
            line.append(word)
            if len(line) >= MAX_WORD_PER_LINE:
                retval.append(' '.join(line))
                line = []

        if len(line) > 0:
            retval.append(' '.join(line))

        return retval

def _create_word_queue(text):
    queue = []
    text = text.strip()
    index = text.find(' ')

    while index >= 0:
        queue.append(text[0:index])
        text = text[index:].lstrip()
        index = text.find(' ')

    if len(text) > 0:
        queue.append(text)

    return queue
