from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QLabel

from album.gui.widgets.util import create_btn


class PreInstallSolutionWidget(QWidget):
    # events
    install_solution = pyqtSignal()
    cancel_solution = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        question = QLabel("This solution isn't installed. Would you like to install it?")
        question.setWordWrap(True)
        self.layout.addWidget(question, 1)
        self.layout.addWidget(self._create_actions_box())
        self._widgets = {}
        self._required = []

    def _create_actions_box(self):
        res = QWidget(self)
        actions_layout = QHBoxLayout(res)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addWidget(create_btn(self, self.cancel_solution, "Cancel", "Esc"))
        self.install_btn = create_btn(self, self.install_solution, "Install", "Enter")
        actions_layout.addWidget(self.install_btn)
        return res

    def set_active(self):
        self.install_btn.setDefault(True)
        self.install_btn.setAutoDefault(True)
        self.install_btn.setFocus()

    def set_not_active(self):
        self.install_btn.setDefault(False)
        self.install_btn.setAutoDefault(False)
