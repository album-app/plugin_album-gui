from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QScrollArea, QFrame, QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton

from album.gui.util import create_btn


class InstallSolutionWidget(QWidget):
    continue_after_install = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.run_output = QLabel()
        self.run_output.setStyleSheet("font-family: monospace;")
        self.scroll_layout.addWidget(self.run_output)
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.setWidgetResizable(True)
        self.scroll.setViewportMargins(0, 0, 0, 0)
        self.scroll.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scroll, 1)
        self.layout.addWidget(self._create_status_box())
        self._last_log = None

    def _create_status_box(self):
        res = QWidget()
        actions_layout = QHBoxLayout(res)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel("Installing...")
        self.status_widget = QProgressBar()
        self.status_widget.setRange(0, 0)
        self.continue_btn = create_btn(self, self.continue_after_install, "Continue", "Enter")
        self.continue_btn.setVisible(False)
        actions_layout.addWidget(self.status_label)
        actions_layout.addWidget(self.status_widget, 1)
        actions_layout.addStretch()
        actions_layout.addWidget(self.continue_btn)
        return res

    def update_solution_log(self, records):
        self.scroll.setFrameShape(QFrame.Box)
        start_i = 0
        if self._last_log:
            for i in range(len(records)):
                if records[i]["msg"] == self._last_log["msg"] and records[i]["asctime"] == self._last_log["asctime"]:
                    start_i = i+1
                    break
        for i in range(start_i, len(records)):
            record = records[i]
            if self.run_output.text():
                self.run_output.setText("%s\n%s" % (self.run_output.text(), record["msg"]))
            else:
                self.run_output.setText("%s" % record["msg"])
        self.scroll_widget.update()
        self._last_log = records[len(records)-1]

    def set_solution_finished(self):
        self.status_widget.setVisible(False)
        self.status_label.setText("Finished.")
        self.continue_btn.setVisible(True)

    def set_solution_failed(self):
        self.status_widget.setVisible(False)
        self.status_label.setText("Failed.")

    def set_active(self):
        self.continue_btn.setDefault(True)
        self.continue_btn.setAutoDefault(True)

    def set_not_active(self):
        self.continue_btn.setDefault(False)
        self.continue_btn.setAutoDefault(False)
