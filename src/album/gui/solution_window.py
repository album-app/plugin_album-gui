from PyQt5.QtCore import pyqtSignal, QEvent, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedLayout, QMainWindow
from album.core.api.model.collection_index import ICollectionIndex

from album.gui.widgets.pre_install_solution_widget import PreInstallSolutionWidget
from album.gui.widgets.pre_run_solution_widget import PreRunSolutionWidget
from album.gui.widgets.solution_status_widget import SolutionStatus


class SolutionWidget(QMainWindow):
    class UninstallSolutionWidget(SolutionStatus):
        def _get_progress_text(self):
            return "Uninstalling..."

        def _get_continue_text(self):
            return "Close"

    class InstallSolutionWidget(SolutionStatus):
        def _get_progress_text(self):
            return "Installing..."

        def _get_continue_text(self):
            return "Run"

    class RunSolutionWidget(SolutionStatus):
        def _get_progress_text(self):
            return "Running..."

        def _get_continue_text(self):
            return "Restart"

    closing = pyqtSignal()
    return_pressed = pyqtSignal(QKeyEvent)
    esc_pressed = pyqtSignal(QKeyEvent)

    INDEX_PRE_INSTALL_SOLUTION = 0
    INDEX_INSTALL_SOLUTION = 1
    INDEX_PRE_RUN_SOLUTION = 2
    INDEX_RUN_SOLUTION = 3
    INDEX_UNINSTALL_SOLUTION = 4

    def __init__(self):
        super().__init__()
        widget = QWidget()
        self.layout = QVBoxLayout(widget)
        self.setCentralWidget(widget)
        self.solution_header = QWidget(self)
        self.stacked_layout = QStackedLayout()
        self.pre_install_widget = PreInstallSolutionWidget(self)
        self.install_widget = SolutionWidget.InstallSolutionWidget(self)
        self.uninstall_widget = SolutionWidget.UninstallSolutionWidget(self)
        self.pre_run_widget = PreRunSolutionWidget(self)
        self.run_widget = SolutionWidget.RunSolutionWidget(self)
        self.layout.addWidget(self.solution_header)
        self.widgets = [self.pre_install_widget, self.install_widget, self.pre_run_widget, self.run_widget,
                        self.uninstall_widget]
        for widget in self.widgets:
            self.stacked_layout.addWidget(widget)
        self.layout.addLayout(self.stacked_layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setCurrentIndex(0)
        self.pre_install_widget.cancel_solution.connect(lambda: self.close())
        self.esc_pressed.connect(lambda: self.close())
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Return:
                self.return_pressed.emit(event)
            if key == Qt.Key_Escape:
                self.esc_pressed.emit(event)
        return super(SolutionWidget, self).eventFilter(source, event)

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        self.closing.emit()

    def set_show_solution(self, solution: ICollectionIndex.ICollectionSolution):
        new_header = QWidget()
        layout = QVBoxLayout()
        new_header.setLayout(layout)
        solution_setup = solution.setup()
        if "title" in solution_setup and solution_setup["title"]:
            title = "%s (version %s)" % (solution_setup["title"], solution_setup["version"])
        else:
            title = "%s:%s:%s" % (solution_setup["group"], solution_setup["name"], solution_setup["version"])
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        if "description" in solution_setup and solution_setup["description"]:
            description = solution_setup["description"]
        else:
            description = "No description provided."
        description_label = QLabel(description)
        description_label.setStyleSheet("color: rgba(0,0,0,0.6)")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        self.layout.replaceWidget(self.solution_header, new_header)
        self.solution_header = new_header

    def show_pre_install(self):
        self._set_active(self.INDEX_PRE_INSTALL_SOLUTION)

    def show_install(self):
        self._set_active(self.INDEX_INSTALL_SOLUTION)

    def show_uninstall(self):
        self._set_active(self.INDEX_UNINSTALL_SOLUTION)

    def show_pre_run(self):
        self._set_active(self.INDEX_PRE_RUN_SOLUTION)

    def show_run(self):
        self._set_active(self.INDEX_RUN_SOLUTION)

    def get_pre_install_widget(self):
        return self.pre_install_widget

    def get_install_widget(self):
        return self.install_widget

    def get_uninstall_widget(self):
        return self.uninstall_widget

    def get_pre_run_widget(self):
        return self.pre_run_widget

    def get_run_widget(self):
        return self.run_widget

    def _set_active(self, index):
        self.stacked_layout.setCurrentIndex(index)
        for i, widget in enumerate(self.widgets):
            if index == i:
                widget.set_active()
            else:
                widget.set_not_active()

    def set_active(self):
        pass

    def set_not_active(self):
        pass
