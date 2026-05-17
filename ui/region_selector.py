from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


class RegionSelector(QWidget):
    """Fullscreen transparent overlay for drag-to-select a capture region."""

    def __init__(self):
        super().__init__()
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self._result = None

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        # Cover all monitors
        desk = QDesktopWidget()
        total = desk.geometry()
        for i in range(desk.screenCount()):
            total = total.united(desk.screenGeometry(i))
        self.setGeometry(total)

    def select(self):
        """Show the overlay, block until user selects a region, return (x,y,w,h) or None."""
        self.show()
        self.raise_()
        self.activateWindow()
        # Run a local event loop until selection is done
        from PyQt5.QtCore import QEventLoop
        loop = QEventLoop()
        self._loop = loop
        loop.exec_()
        self.hide()
        return self._result

    def paintEvent(self, event):
        painter = QPainter(self)
        # Dim the whole screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._selecting:
            sel = self._selection_rect()
            # Clear (brighten) the selected area
            painter.fillRect(sel, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(sel, QColor(255, 255, 255, 255))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Border
            pen = QPen(QColor(80, 160, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(sel)

            # Dimension label
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Consolas", 10))
            label = f"{sel.width()} × {sel.height()}"
            lx = sel.right() - 100 if sel.right() > 110 else sel.left() + 4
            ly = sel.bottom() + 16 if sel.bottom() + 20 < self.height() else sel.top() - 6
            painter.drawText(lx, ly, label)
        else:
            # Instruction text
            painter.setPen(QColor(255, 255, 255, 180))
            painter.setFont(QFont("Segoe UI", 14))
            painter.drawText(
                self.rect(), Qt.AlignCenter,
                "Click and drag to select a region\nPress Escape to cancel"
            )

    def _selection_rect(self):
        return QRect(self._origin, self._current).normalized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            sel = self._selection_rect()
            if sel.width() > 10 and sel.height() > 10:
                # Convert to global screen coordinates
                geo = self.geometry()
                self._result = (
                    geo.x() + sel.x(),
                    geo.y() + sel.y(),
                    sel.width(),
                    sel.height(),
                )
            else:
                self._result = None
            if hasattr(self, "_loop"):
                self._loop.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._result = None
            self._selecting = False
            if hasattr(self, "_loop"):
                self._loop.quit()
