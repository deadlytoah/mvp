"""Use an algorithm based on graph to layout words in the flash
card"""

import networkx as nx

MAX_WORD_PER_LINE = 6
START_NODE = 'START'
END_NODE = 'END'

class GraphLayout:
    def layout(self, text):
        retval = []
        queue = _create_word_queue(text)
        line = []

        # nodeid is a sequential integer that is uniquely assigned to
        # each node.  This is required since the text cannot be used
        # to uniquly identify each node as some nodes have the same
        # text.
        nodeid = 0

        graph = nx.DiGraph()
        graph.add_node(nodeid, text=START_NODE, level=0)
        nodeid += 1

        for i, word in enumerate(queue):
            level = i + 1
            wordid = nodeid
            nodeid += 1
            graph.add_node(wordid, text=word, level=level)

            for node in graph.nodes():
                if graph.node[node]['level'] == level - 1:
                    if graph.node[node]['text'] != START_NODE:
                        newnodeid = nodeid
                        nodeid += 1
                        newnode = ' '.join([graph.node[node]['text'], word])
                        graph.add_node(newnodeid, text=newnode, level=level)
                        for pred in graph.predecessors(node):
                            graph.add_edge(pred, newnodeid)

                    graph.add_edge(node, wordid)

        endnodeid = nodeid
        nodeid += 1
        graph.add_node(endnodeid, text=END_NODE, level=len(queue) + 1)
        for node in graph.nodes():
            if graph.node[node]['level'] == len(queue):
                graph.add_edge(node, endnodeid)

        self.graph = graph
        self.maxlevel = len(queue) + 2

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
