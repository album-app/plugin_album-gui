from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit

from album.gui.widgets.util import create_btn, get_monospace_font


class SolutionStatus(QWidget):
    continue_signal = pyqtSignal()
    cancel_signal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.run_output = QTextEdit()
        self.run_output.setReadOnly(True)
        self.run_output.setWordWrapMode(1)  # Word wrap
        self.run_output.setFont(get_monospace_font())
        self.layout.addWidget(self.run_output, 1)
        self.layout.addWidget(self._create_status_box())

    def _create_status_box(self):
        res = QWidget(self)
        actions_layout = QHBoxLayout(res)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel(self._get_progress_text())
        self.status_widget = QProgressBar()
        self.status_widget.setRange(0, 0)
        # self.cancel_btn = create_btn(self, self.cancel_installation, "Cancel", "Esc")
        # self.cancel_btn.setVisible(True)
        self.continue_btn = create_btn(self, self.continue_signal, self._get_continue_text(), "Enter")
        self.continue_btn.setVisible(False)
        actions_layout.addWidget(self.status_label)
        actions_layout.addWidget(self.status_widget, 1)
        actions_layout.addStretch()
        # actions_layout.addWidget(self.cancel_btn)
        actions_layout.addWidget(self.continue_btn)
        return res

    def update_solution_log(self, record):
        if hasattr(record, "msg"):
            self.run_output.append(record.msg)
        else:
            self.run_output.append(record["msg"])
        # self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        self.set_active()

    def set_solution_unfinished(self):
        self.status_widget.setVisible(True)
        self.status_label.setText(self._get_progress_text())
        self.continue_btn.setVisible(False)

    def set_solution_finished(self):
        self.status_widget.setVisible(False)
        self.status_label.setText(self._get_finished_text())
        self.continue_btn.setVisible(True)
        # self.cancel_btn.setVisible(False)

    def set_solution_failed(self):
        self.status_widget.setVisible(False)
        self.status_label.setText(self._get_failed_text())
        # self.cancel_btn.setVisible(False)

    def set_active(self):
        self.continue_btn.setDefault(True)
        self.continue_btn.setAutoDefault(True)

    def set_not_active(self):
        self.continue_btn.setDefault(False)
        self.continue_btn.setAutoDefault(False)

    def _get_continue_text(self):
        return "Continue"

    def _get_progress_text(self):
        return "Uninstalling..."

    def _get_failed_text(self):
        return "Failed."

    def _get_finished_text(self):
        return "Finished."
