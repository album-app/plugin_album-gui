import pkg_resources
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QHBoxLayout, QScrollArea, QFrame, QWidget, QVBoxLayout, QLabel

from album.gui.util import create_btn


class PreRunSolutionWidget(QWidget):
    # events
    run_solution = pyqtSignal()
    cancel_solution = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._load_plugins()
        # gui
        self.layout = QVBoxLayout(self)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(scroll_widget)
        self.scroll.setWidgetResizable(True)
        self.scroll.setViewportMargins(0, 0, 0, 0)
        self.scroll.setContentsMargins(0, 0, 0, 0)
        self.required_warning = self._create_warning_msg()
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.required_warning)
        self.layout.addWidget(self._create_actions_box())
        self._widgets = {}
        self._required = []

    def _create_actions_box(self):
        res = QWidget()
        actions_layout = QHBoxLayout(res)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addWidget(create_btn(self, self.cancel_solution, "Cancel", "Esc"))
        self.run_btn = create_btn(self, self.run_solution, "Run", "Enter")
        self.run_btn.setDefault(True)
        self.run_btn.setAutoDefault(True)
        actions_layout.addWidget(self.run_btn)
        return res

    def _load_plugins(self):
        self._plugins = {}
        for entry_point in pkg_resources.iter_entry_points('album_gui_plugins'):
            # try:
            #     entry_point.load()
            #     self._plugins[entry_point.name] = entry_point.load()
            # except Exception as e:
            #     get_active_logger().error("Cannot load GUI plugin %s" % entry_point.name)
            #     get_active_logger().error(str(e))
            entry_point.load()
            self._plugins[entry_point.name] = entry_point.load()

    def add_argument(self, argument):
        self.scroll.setFrameShape(QFrame.Box)
        arg_name = argument["name"]
        if "required" in argument:
            if argument["required"] and arg_name not in self._required:
                self._required.append(arg_name)
        if "type" in argument:
            arg_type = argument["type"]
        else:
            arg_type = "string"
        if arg_type not in self._plugins:
            arg_type = "string"
        widget = self._plugins[arg_type](argument)

        self._widgets[arg_name] = widget
        self.scroll_layout.addWidget(widget)

    def get_values(self):
        res = {}
        for name in self._widgets:
            res[name] = self._widgets[name].get_value()
        return res

    def check_required_fields(self) -> bool:
        values = self.get_values()
        missing_values = []
        for name in self._required:
            assert name in values
            value = values[name]
            if not value:
                missing_values.append(name)
        if missing_values:
            self.required_warning.setVisible(True)
            self._highlight_missing_values(missing_values)
            return False
        else:
            self.required_warning.setVisible(False)
        return True

    def _highlight_missing_values(self, values):
        for name in self._widgets:
            widget = self._widgets[name]
            if name in values:
                widget.setStyleSheet("QGroupBox{border: 1px solid red;}")
                widget.repaint()
            else:
                widget.setStyleSheet("")

    @staticmethod
    def _create_warning_msg():
        res = QLabel("Please provide the missing required arguments.")
        res.setWordWrap(True)
        res.setStyleSheet("color: red;")
        res.setVisible(False)
        return res

    def set_active(self):
        self.run_btn.setDefault(True)
        self.run_btn.setAutoDefault(True)

    def set_not_active(self):
        self.run_btn.setDefault(False)
        self.run_btn.setAutoDefault(False)
