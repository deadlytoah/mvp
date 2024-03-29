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
        highway['middle'] = highway['y'] + highway['height'] // 2

        cumwidth = 0
        lanes = []
        for level in range(0, self.maxlevel):
            lanes.append({
                'nodes': [],
                'width': 250,
                'x': level * 250
            })

            lane = lanes[-1]
            lane['x'] = cumwidth + MARGIN['x']
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
                                          node['y'] + node['height'] // 2),
                    'east': QtCore.QPoint(lane['x'] + node['width'] + 1,
                                          node['y'] + node['height'] // 2)
                }

                costfont = QtGui.QFont(self.font())
                costfont.setPointSize(9)
                socketeast = node['sockets']['east']
                node['cost'] = self.graph.node[nodeid]['cost']
                node['costcolor'] = QtGui.QColor('gray')
                node['costfont'] = costfont
                node['costpoint'] = QtCore.QPoint(socketeast.x() + 1,
                                                  socketeast.y() - 1)

                # drawrect causes the nodes to be drawn if it
                # intersects with the view's event rect.
                COST_WIDTH = 30
                drawrect = QtCore.QRect(lane['x'],
                                        node['y'],
                                        node['width'] + COST_WIDTH,
                                        node['height'])
                node['drawrect'] = drawrect

                node['successors'] = {
                    'near': [s for s in self.graph.successors(node['id'])
                             if self.graph.node[s]['level'] == level + 1],
                    'far': [s for s in self.graph.successors(node['id'])
                            if self.graph.node[s]['level'] > level + 1]
                }

                lane['nodes'].append(node)

            lane['width'] = max([node['width'] for node in lane['nodes']])
            lane['height'] = cumheight
            cumwidth += lane['width'] + MARGIN['x']

        self.setMinimumSize(cumwidth + MARGIN['x'],
                            max([lane['height'] for lane in lanes])
                            + MARGIN['y'])

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

            # drawrect causes the connection to be drawn if it
            # intersects with the view's event rect
            conn['drawrect']= QtCore.QRect(start, end)

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
            draw_node = _draw_node
            draw_cost = _draw_cost
            eventrect = event.rect()
            intersect = eventrect.intersects
            for lane in self.graphview['lanes']:
                x = lane['x']
                for node in lane['nodes']:
                    if intersect(node['drawrect']):
                        y = node['y']
                        size = node['rectsize']
                        draw_node(qp,
                                  QtCore.QRectF(x,
                                                y,
                                                size.width(),
                                                size.height()),
                                  node['font'],
                                  node['color'],
                                  node['fillcolor'],
                                  node['lines'])
                        draw_cost(qp,
                                  node['costpoint'],
                                  node['costfont'],
                                  node['costcolor'],
                                  node['cost'])

            highway = self.graphview['highway']
            qp.setPen(QtGui.QPen(QtGui.QColor('lightgray'), 1.5))
            qp.drawLine(highway['begin'],
                        highway['middle'],
                        highway['end'],
                        highway['middle'])

            draw_conn = _draw_connection
            for conn in self.graphview['conns']:
                if intersect(conn['drawrect']):
                    draw_conn(qp,
                              conn['points'],
                              conn['color'],
                              conn['arrow'])

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

def _draw_connection(qp, points, color, arrow):
    qp.setPen(QtGui.QPen(color, 1))

    qpp = QtGui.QPainterPath(points[0])
    qpp.cubicTo(points[1], points[2], points[3])
    qp.drawPath(qpp)

    if arrow:
        _draw_arrow(qp, points, color)

def _draw_arrow(qp, points, color):
    qpp = QtGui.QPainterPath(points[3])
    qpp.lineTo(points[3].x() - 6, points[3].y() - 5)
    qpp.lineTo(points[3].x() - 6, points[3].y() + 5)
    qp.fillPath(qpp, color)
