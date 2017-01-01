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
            'height': 50,
            'payloads': []
        }
        highway['middle'] = highway['y'] + int(highway['height'] / 2)

        cumwidth = 0
        lanes = []
        for level in range(0, self.maxlevel):
            lanes.append({
                'nodes': [],
                'width': 250,
                'x': level * 250
            })

            lane = lanes[-1]
            lane['x'] = cumwidth + level * MARGIN['x'] + MARGIN['x']
            cumheight = 0

            for i, nodeid in enumerate([nodeid for nodeid in self.graph.nodes() if self.graph.node[nodeid]['level'] == level]):
                node = {
                    'id': nodeid,
                    'font': self.font(),
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

                # Nodes that are selected by the algorithm are
                # highlighted.
                if nodeid in self.engine.shortest_path:
                    node['color'] = QtGui.QColor('red')
                    node['fillcolor'] = QtGui.QColor('white')
                    node['selected'] = True
                else:
                    node['color'] = QtGui.QColor('black')
                    node['fillcolor'] = QtGui.QColor('white')
                    node['selected'] = False

                cumheight += MARGIN['y'] + node['height']

                # Leave a room between some nodes for the highway.
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

                costfont = QtGui.QFont(self.font())
                costfont.setPointSize(9)
                socketeast = node['sockets']['east']
                node['cost'] = self.graph.node[nodeid]['cost']
                node['costcolor'] = QtGui.QColor('gray')
                node['costfont'] = costfont
                node['costpoint'] = QtCore.QPoint(socketeast.x() + 1,
                                                  socketeast.y() - 1)

                node['successors'] = {
                    'near': [s for s in self.graph.successors(node['id'])
                             if self.graph.node[s]['level'] == level + 1],
                    'far': [s for s in self.graph.successors(node['id'])
                            if self.graph.node[s]['level'] > level + 1]
                }

                lane['nodes'].append(node)

            lane['width'] = max([node['width'] for node in lane['nodes']])
            cumwidth += lane['width']

        # Collect all necessary information for rendering the
        # edges.
        conns = []
        for level, lane in enumerate(lanes):
            for node in lane['nodes']:
                for successor in node['successors']['near']:
                    nextlane = lanes[level + 1]
                    successor = [node for node in nextlane['nodes']
                                 if node['id'] == successor][0]
                    selected = node['selected'] and successor['selected']
                    conns.append({
                        'lanes': (lane, nextlane),
                        'sockets': (node['sockets']['east'],
                                    successor['sockets']['west']),
                        'arrow': True,
                        'selected': selected
                    })

                for successorid in node['successors']['far']:
                    successor = self.graph.node[successorid]
                    destnodevm = [nodevm
                        for nodevm in lanes[successor['level']]['nodes']
                        if nodevm['id'] == successorid][0]
                    destsocket = destnodevm['sockets']['west']
                    selected = node['selected'] and destnodevm['selected']

                    payload = {
                        'srcsocket': node['sockets']['east'],
                        'srclevel': level,
                        'destsocket': destsocket,
                        'destlevel': successor['level'],
                        'selected': selected
                    }
                    highway['payloads'].append(payload)

        highway['begin'] = cumwidth
        highway['end'] = 0
        highway['selected'] = []

        for payload in highway['payloads']:
            # selected sections of the highway are highlighted.
            selected = [0, 0]

            # onlamps
            lane = lanes[payload['srclevel']]
            nextlane = lanes[payload['srclevel'] + 1]
            conn = {
                'lanes': (lane, nextlane),
                'sockets': (payload['srcsocket'],
                            QtCore.QPoint(nextlane['x'], highway['middle'])),
                'arrow': False,
                'selected': payload['selected']
            }
            conns.append(conn)
            highway['begin'] = min(highway['begin'], conn['sockets'][1].x())
            if payload['selected']:
                selected[0] = conn['sockets'][1].x()

            # offlamps
            lane = lanes[payload['destlevel']]
            prevlane = lanes[payload['destlevel'] - 1]
            conn = {
                'lanes': (prevlane, lane),
                'sockets': (QtCore.QPoint(prevlane['x'] + prevlane['width'],
                                          highway['middle']),
                            payload['destsocket']),
                'arrow': True,
                'selected': payload['selected']
            }
            conns.append(conn)
            highway['end'] = max(highway['end'], conn['sockets'][0].x())
            if payload['selected']:
                selected[1] = conn['sockets'][0].x()

            highway['selected'].append(selected)

        # Priority connections are painted over the normal ones.
        # These are the connections that are highlighted because they
        # are selected by the algorithm.
        priority = []
        normal = []

        # produce Bezier control points from the connection parameters
        for conn in conns:
            start = conn['sockets'][0]
            end = conn['sockets'][1]
            c1 = QtCore.QPoint(conn['lanes'][1]['x'], start.y())
            c2 = QtCore.QPoint(conn['lanes'][0]['x']
                               + conn['lanes'][0]['width'],
                               end.y())
            conn['points'] = [start, c1, c2, end]

            if conn['selected']:
                conn['color'] = QtGui.QColor('red')
                priority.append(conn)
            else:
                conn['color'] = QtGui.QColor('lightgray')
                normal.append(conn)

        # The graph view, ready to be painted...
        self.graphview = {
            'lanes': lanes,
            'conns': normal + priority,
            'highway': highway
        }

        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.graphview != None:
            for lane in self.graphview['lanes']:
                x = lane['x']
                for node in lane['nodes']:
                    y = node['y']
                    size = node['rectsize']
                    rect = QtCore.QRectF(x, y, size.width(), size.height())
                    font = node['font']
                    color = node['color']
                    fillcolor = node['fillcolor']

                    _draw_node(qp, rect, font, color, fillcolor, node['lines'])
                    _draw_cost(qp,
                               node['costpoint'],
                               node['costfont'],
                               node['costcolor'],
                               node['cost'])

                    while rect.x() + rect.width() > self.minimumWidth():
                        self._expand_horizontally()
                    while rect.y() + rect.height() > self.minimumHeight():
                        self._expand_vertically()

            highway = self.graphview['highway']
            qp.setPen(QtGui.QPen(QtGui.QColor('lightgray'), 1.5))
            qp.drawLine(highway['begin'],
                        highway['middle'],
                        highway['end'],
                        highway['middle'])

            for conn in self.graphview['conns']:
                qp.setPen(QtGui.QPen(conn['color'], 1))

                points = conn['points']

                qpp = QtGui.QPainterPath(points[0])
                qpp.cubicTo(points[1], points[2], points[3])
                qp.drawPath(qpp)

                if conn['arrow']:
                    qpp = QtGui.QPainterPath(points[3])
                    qpp.lineTo(points[3].x() - 6, points[3].y() - 5)
                    qpp.lineTo(points[3].x() - 6, points[3].y() + 5)
                    qp.fillPath(qpp, conn['color'])

            qp.setPen(QtGui.QPen(QtGui.QColor('red'), 1))
            for selected in highway['selected']:
                qp.drawLine(selected[0],
                            highway['middle'],
                            selected[1],
                            highway['middle'])

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

def _draw_node(qp, rectf, font, color, fillcolor, lines):
    path = QtGui.QPainterPath()
    path.addRoundedRect(rectf, 4, 4)
    pen = QtGui.QPen(color, 1)
    qp.setPen(pen)
    qp.fillPath(path, fillcolor)
    qp.drawPath(path)

    # use clipping so the text doesn't escape the rectangle.
    qp.setClipPath(path)

    qp.setFont(font)
    rectf.adjust(PADDING, PADDING, -PADDING, -PADDING)
    qp.drawText(rectf, '\n'.join(lines))
    qp.setClipPath(path, QtCore.Qt.NoClip)

def _draw_cost(qp, point, font, color, cost):
    qp.setFont(font)
    qp.setPen(QtGui.QPen(color, 1))
    qp.drawText(point, format(cost, '.2f'))
