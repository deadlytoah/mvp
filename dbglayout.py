# coding: utf-8
"""Lets you test out the layout engine for debugging."""

from PyQt5 import QtCore, QtGui, QtWidgets

class DbgLayout(QtWidgets.QDialog):
    """dialog for testing out the layout engine"""
    def __init__(self, parent = None):
        super(DbgLayout, self).__init__(parent)

        self.setWindowTitle('Debug – Test Layout Engines')
        self.resize(800, 500)

        self.boxes = []
        self.box_in_use = 0

        # set up the 3 by 3 boxes.
        self.setLayout(QtWidgets.QVBoxLayout())
        for _ in range(3):
            row = QtWidgets.QWidget(self)
            row.setLayout(QtWidgets.QHBoxLayout())
            self.layout().addWidget(row)

            for _ in range(3):
                self.boxes.append(DbgLayoutBox(row))
                row.layout().addWidget(self.boxes[-1])

    def set_text(self, text):
        for box in self.boxes:
            box.set_text(text)

    def add_layout_engine(self, layout_engine):
        if self.box_in_use < len(self.boxes):
            self.boxes[self.box_in_use].set_layout_engine(layout_engine)
            self.box_in_use += 1
            return True
        else:
            return False

class DbgLayoutBox(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(DbgLayoutBox, self).__init__(parent)
        self.text = ''
        self.engine = None

    def set_text(self, text):
        self.text = text

    def set_layout_engine(self, engine):
        self.engine = engine

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setPen(QtGui.QColor('black'))
        qp.setFont(QtGui.QFont('Serif', 9))

        if self.engine != None:
            lines = self.engine.layout(self.text)
            middle = len(lines) / 2

            for i, line in enumerate(lines):
                self._text_line(qp, event, i - middle, line)
        else:
            self._empty_view(qp, event)

        qp.end()

    def _text_line(self, qp, event, offset, line):
        rect = event.rect()
        rect.moveTop(offset * 20)
        qp.drawText(rect, QtCore.Qt.AlignCenter, line)

    def _empty_view(self, qp, event):
        qp.setPen(QtGui.QColor('lightgray'))
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, "Empty View")

if __name__ == '__main__':
    import sys

    class TestEngine():
        def layout(self, verse):
            s = []
            s.append(verse[:33])
            s.append(verse[33:81])
            s.append(verse[81:])
            return s

    app = QtWidgets.QApplication(sys.argv)

    # invisible parent window for our QDialog
    window = QtWidgets.QMainWindow()

    dbglayout = DbgLayout(window)
    dbglayout.set_text('Paul and Timothy, bondservants of Jesus Christ, To all the saints in Christ Jesus who are in Philippi, with the bishops and deacons:')
    assert(dbglayout.add_layout_engine(TestEngine()))
    dbglayout.show()
    sys.exit(app.exec())
