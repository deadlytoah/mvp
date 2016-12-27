# coding: utf-8
"""Implements a debug screen for displaying layout graph."""

from math import sqrt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from graphlayout import GraphLayout
from simplelayout import SimpleLayout

PADDING = 5
MARGIN = {
    'x': 50,
    'y': 15
}

window = None

class DbgGraph:
    """Displays and implements the debug screen for layout graph."""
    def __init__(self):
        global window
        window = self

        self.gui = uic.loadUi("dbggraph.ui")

        self.canvas = GraphCanvas()
        self.gui.scroll_area.setWidget(self.canvas)

    def set_text(self, text):
        self.gui.lineedit_sentence.setText(text)
        self.canvas.set_text(text)
        self.canvas.update_view()

class GraphCanvas(QtWidgets.QWidget):
    def __init__(self):
        super(GraphCanvas, self).__init__()
        self.text = None
        self.engine = GraphLayout()
        self.graph = None
        self.graphview = None

    def set_text(self, text):
        self.text = text

    def update_view(self):
        self.engine.layout(self.text)
        self.graph = self.engine.graph
        self.maxlevel = self.engine.maxlevel

        highway = {
            'y': 300,
            'height': 50
        }

        cumwidth = 0
        lanes = []
        for level in range(0, self.maxlevel):
            lanes.append({
                'nodes': [],
                'color': QtGui.QColor('black'),
                'fillcolor': QtGui.QColor('white'),
                'width': 250,
                'x': level * 250
            })

            lane = lanes[-1]
            lane['x'] = cumwidth + level * MARGIN['x'] + MARGIN['x']
            cumheight = 0

            for i, nodeid in enumerate([nodeid for nodeid in self.graph.nodes() if self.graph.node[nodeid]['level'] == level]):
                node = {
                    'id': nodeid,
                    'text': self.graph.node[nodeid]['text']
                }
                node['lines'] = self._layout_text(node['text'])

                # find a big enough size for the round rectangle
                # to fit the entire text.
                textsize = self._size_up_text(node['lines'])
                node['textsize'] = textsize
                node['rectsize'] = QtCore.QSize(textsize.width() + PADDING * 2 + 1, textsize.height() + PADDING * 2 + 1)
                node['width'] = node['rectsize'].width()
                node['height'] = node['rectsize'].height()
                node['y'] = MARGIN['y'] + cumheight
                cumheight += MARGIN['y'] + node['height']

                if highway['y'] <= node['y'] <= highway['y'] + highway['height'] or \
                   highway['y'] <= node['y'] + node['height'] <= highway['y'] + highway['height']:
                    node['y'] = highway['y'] + highway['height']
                    cumheight = node['y'] + node['height']

                node['sockets'] = {
                    'west': QtCore.QPoint(lane['x'] - 1,
                                          node['y'] + node['height'] / 2),
                    'east': QtCore.QPoint(lane['x'] + node['width'] + 1,
                                          node['y'] + node['height'] / 2)
                }

                node['successors'] = {
                    'near': [s for s in self.graph.successors(node['id'])
                             if self.graph.node[s]['level'] == level + 1],
                    'far': [s for s in self.graph.successors(node['id'])
                            if self.graph.node[s]['level'] > level + 1]
                }

                lane['nodes'].append(node)

            lane['width'] = max([node['width'] for node in lane['nodes']])
            cumwidth += lane['width']

        # distinct colours for START and END nodes
        lanes[0]['color'] = QtGui.QColor('red')
        lanes[-1]['color'] = QtGui.QColor('red')

        conns = []
        for i, lane in enumerate(lanes):
            for node in lane['nodes']:
                for successor in node['successors']['near']:
                    nextlane = lanes[i + 1]
                    successor = [node for node in nextlane['nodes']
                                 if node['id'] == successor][0]
                    start = node['sockets']['east']
                    end = successor['sockets']['west']
                    c1 = QtCore.QPoint((end.x() + start.x()) / 2,
                                       start.y())
                    c2 = QtCore.QPoint(c1.x(), end.y())
                    conns.append([start, c1, c2, end])

        self.graphview = {
            'lanes': lanes,
            'conns': conns
        }

        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.graphview != None:
            for lane in self.graphview['lanes']:
                x = lane['x']
                color = lane['color']
                fillcolor = lane['fillcolor']
                for node in lane['nodes']:
                    y = node['y']
                    size = node['rectsize']
                    rect = QtCore.QRectF(x, y, size.width(), size.height())

                    _draw_node(qp, rect, color, fillcolor, node['lines'])

                    while rect.x() + rect.width() > self.minimumWidth():
                        self._expand_horizontally()
                    while rect.y() + rect.height() > self.minimumHeight():
                        self._expand_vertically()

            pen = QtGui.QPen(QtGui.QColor('dark gray'), 1)
            qp.setPen(pen)

            for conn in self.graphview['conns']:
                qpp = QtGui.QPainterPath(conn[0])
                qpp.cubicTo(conn[1], conn[2], conn[3])
                qp.drawPath(qpp)

                qpp = QtGui.QPainterPath(conn[3])
                qpp.lineTo(conn[3].x() - 6, conn[3].y() - 5)
                qpp.lineTo(conn[3].x() - 6, conn[3].y() + 5)
                qp.fillPath(qpp, QtGui.QColor('black'))

        qp.end()

    def _layout_text(self, text):
        # equation for spliting up the text proportionately.
        width = int(sqrt(35 / 3 * len(text)))

        sl = SimpleLayout()
        sl.set_line_width(width)
        return sl.layout(text)

    def _size_up_text(self, lines):
        fm = QtGui.QFontMetrics(self.font())
        maxwidth = 0
        for line in lines:
            maxwidth = max([maxwidth, fm.width(line)])
        height = fm.height() * len(lines)
        return QtCore.QSize(maxwidth, height)

    def _expand_horizontally(self):
        if self.minimumWidth() == 0:
            self.setMinimumWidth(self.width())
        else:
            self.setMinimumWidth(2 * self.minimumWidth())

    def _expand_vertically(self):
        if self.minimumHeight() == 0:
            self.setMinimumHeight(self.height())
        else:
            self.setMinimumHeight(2 * self.minimumHeight())

def _draw_node(qp, rectf, color, fillcolor, lines):
    path = QtGui.QPainterPath()
    path.addRoundedRect(rectf, 4, 4)
    pen = QtGui.QPen(color, 1)
    qp.setPen(pen)
    qp.fillPath(path, fillcolor)
    qp.drawPath(path)

    # use clipping so the text doesn't escape the rectangle.
    qp.setClipPath(path)

    rectf.adjust(PADDING, PADDING, -PADDING, -PADDING)
    qp.drawText(rectf, '\n'.join(lines))
    qp.setClipPath(path, QtCore.Qt.NoClip)
