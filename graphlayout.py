"""Use an algorithm based on graph to layout words in the flash
card"""

import networkx as nx

OPTIMAL_LINE_WIDTH = 35
START_NODE = 'START'
END_NODE = 'END'

class GraphLayout:
    def layout(self, text):
        queue = _create_word_queue(text)

        # nodeid is a sequential integer that is uniquely assigned to
        # each node.  This is required since the text cannot be used
        # to uniquly identify each node as some nodes have the same
        # text.
        nodeid = 0

        graph = nx.DiGraph()
        self.graph = graph
        startnodeid = nodeid
        graph.add_node(startnodeid, text=START_NODE, level=0, cost=0)
        nodeid += 1

        for i, word in enumerate(queue):
            level = i + 1
            wordid = nodeid
            nodeid += 1
            graph.add_node(wordid, text=word, level=level, cost=0)
            self._assign_cost(wordid)

            for node in graph.nodes():
                if graph.node[node]['level'] == level - 1:
                    if graph.node[node]['text'] != START_NODE:
                        newnodeid = nodeid
                        nodeid += 1
                        newnode = ' '.join([graph.node[node]['text'], word])
                        graph.add_node(newnodeid,
                                       text=newnode,
                                       level=level,
                                       cost=0)
                        self._assign_cost(newnodeid)
                        for pred in graph.predecessors(node):
                            graph.add_edge(pred,
                                           newnodeid,
                                           cost=graph.node[pred]['cost'])

                    graph.add_edge(node,
                                   wordid,
                                   cost=graph.node[node]['cost'])

        endnodeid = nodeid
        nodeid += 1
        graph.add_node(endnodeid, text=END_NODE, level=len(queue) + 1)
        for node in graph.nodes():
            if graph.node[node]['level'] == len(queue):
                graph.add_edge(node,
                               endnodeid,
                               cost=graph.node[node]['cost'])

        self.maxlevel = len(queue) + 2

        self.shortest_path = nx.shortest_path(graph,
                                              source=startnodeid,
                                              target=endnodeid,
                                              weight='cost')

        return [graph.node[nodeid]['text']
                for nodeid
                in self.shortest_path[1 : len(self.shortest_path) - 1]]

    def _assign_cost(self, nodeid):
        node = self.graph.node[nodeid]
        node['cost'] += _line_length_cost(node['text'])


def _line_length_cost(text):
    length = len(text)
    return 0.01 * pow(length - OPTIMAL_LINE_WIDTH, 2)

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
