import config
from key import Key

def sentences_cons2(records):
    sentences = []
    lookup = []
    verseseq = [rec['text'] for rec in records]

    # step 1 split verses into a queue of partial or whole verses.
    indiciesseq = [sorted(_find_all_delimiters(text, config.SENTENCE_DELIMITERS))
                   for text in verseseq]
    splitsseq = []
    for i, text in enumerate(verseseq):
        splitsseq.append(_split_verse(i + 1, text, indiciesseq[i]))

    # flatten list of lists
    queue = [split for splits in splitsseq for split in splits]

    # step 2 process the queue to produce sentences and look up table.
    sentence = {
        'text': '',
        'textseq': [],
        'sources': []
    }
    for split in queue:
        sentence['textseq'].append(split['text'])
        sentence['sources'].append({
            'verse': split['origin'],
            'partid': split['partid'],
            'iswhole': split['iswhole']
        })

        if len(lookup) < split['origin']:
            lookup.append(len(sentences))

        if split['isfinal']:
            sentence['text'] = ' '.join(sentence['textseq'])
            sentences.append(sentence)
            sentence = {
                'text': '',
                'textseq': [],
                'sources': []
            }

    return (sentences, lookup)

def sentences_index_by_verseno(sentences, lookup, verseno):
    i = int(verseno) - 1
    return lookup[i]

def sentence_make_label(sentence, book, chapter):
    srclist = []
    sources = sentence['sources']
    for source in sources:
        if source['iswhole']:
            srclist.append(str(source['verse']))
        else:
            srclist.append(str(source['verse']) + chr(ord('a') + source['partid']))
    return book + ' ' + str(chapter) + ':' + ', '.join(srclist)

def _split_verse(verse, text, indices):
    split = []
    start = 0

    # use of lstrip() is due to a whitespace that follows a
    # punctuation.
    for j, index in enumerate(indices):
        split.append({
            'text': text[start:index + 1].lstrip(),
            'partid': j,
            'origin': verse,
            'isfinal': True,
            'iswhole': False
        })
        start = index + 1

    if len(text[start:]) > 0:
        split.append({
            'text': text[start:].lstrip(),
            'partid': len(split),
            'origin': verse,
            'isfinal': False,
            'iswhole': False
        })

    if len(split) == 1:
        split[0]['iswhole'] = True

    return split

def _find_all_delimiters(text, delimiters):
    indicies = []
    for delim in delimiters:
        index = text.find(delim, 0)
        while index >= 0:
            indicies.append(index)
            start = index
            index = text.find(delim, start + 1)
    return indicies
