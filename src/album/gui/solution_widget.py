from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedLayout
from album.core.api.model.collection_index import ICollectionIndex
from album.core.api.model.collection_solution import ICollectionSolution

from album.gui.install_solution_widget import InstallSolutionWidget
from album.gui.pre_install_solution_widget import PreInstallSolutionWidget
from album.gui.pre_run_solution_widget import PreRunSolutionWidget
from album.gui.run_solution_widget import RunSolutionWidget


class SolutionWidget(QWidget):
    INDEX_PRE_INSTALL_SOLUTION = 0
    INDEX_INSTALL_SOLUTION = 1
    INDEX_PRE_RUN_SOLUTION = 2
    INDEX_RUN_SOLUTION = 3

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.solution_header = QWidget()
        self.stacked_layout = QStackedLayout()
        self.pre_install_widget = PreInstallSolutionWidget(self)
        self.install_widget = InstallSolutionWidget(self)
        self.pre_run_widget = PreRunSolutionWidget(self)
        self.run_widget = RunSolutionWidget(self)
        self.layout.addWidget(self.solution_header)
        self.widgets = [self.pre_install_widget, self.install_widget, self.pre_run_widget, self.run_widget]
        for widget in self.widgets:
            self.stacked_layout.addWidget(widget)
        self.layout.addLayout(self.stacked_layout)

    def set_show_solution(self, solution: ICollectionIndex.ICollectionSolution):
        new_header = QWidget()
        layout = QVBoxLayout()
        new_header.setLayout(layout)
        solution_setup = solution.setup()
        if "title" in solution_setup and solution_setup["title"]:
            title = solution_setup["title"]
        else:
            title = "%s:%s:%s" % (solution_setup["group"], solution_setup["name"], solution_setup["version"])
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        if "description" in solution_setup and solution_setup["description"]:
            description = solution_setup["description"]
        else:
            description = "No description provided."
        description_label = QLabel(description)
        description_label.setStyleSheet("color: rgba(0,0,0,0.6)")
        layout.addWidget(description_label)
        self.layout.replaceWidget(self.solution_header, new_header)
        self.solution_header = new_header

    def show_pre_install(self, solution):
        self.set_show_solution(solution)
        self._set_active(self.INDEX_PRE_INSTALL_SOLUTION)

    def show_install(self, solution):
        self.set_show_solution(solution)
        self._set_active(self.INDEX_INSTALL_SOLUTION)

    def show_pre_run(self, solution):
        self.set_show_solution(solution)
        self._set_active(self.INDEX_PRE_RUN_SOLUTION)

    def show_run(self, solution):
        self.set_show_solution(solution)
        self._set_active(self.INDEX_RUN_SOLUTION)

    def get_pre_install_widget(self):
        return self.pre_install_widget

    def get_install_widget(self):
        return self.install_widget

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
