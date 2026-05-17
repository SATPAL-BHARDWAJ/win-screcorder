from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt

from utils.win_utils import enumerate_windows


class WindowPicker(QDialog):
    """Dialog that lists open windows for the user to pick one."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Window to Capture")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(480, 380)
        self._hwnd = None
        self._windows = []
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter windows…")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._accept_item)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("Capture this window")
        btn_ok.clicked.connect(self._accept_selection)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _populate(self):
        self._windows = enumerate_windows()
        self._render(self._windows)

    def _render(self, windows):
        self._list.clear()
        for hwnd, title in windows:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, hwnd)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _filter(self, text):
        q = text.lower()
        filtered = [(h, t) for h, t in self._windows if q in t.lower()]
        self._render(filtered)

    def _accept_item(self, item):
        self._hwnd = item.data(Qt.UserRole)
        self.accept()

    def _accept_selection(self):
        item = self._list.currentItem()
        if item:
            self._hwnd = item.data(Qt.UserRole)
            self.accept()

    def pick(self):
        """Show dialog, return HWND or None."""
        result = self.exec_()
        return self._hwnd if result == QDialog.Accepted else None
