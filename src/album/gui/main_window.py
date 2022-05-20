from PyQt5.QtWidgets import QStackedLayout, QDialog

from album.gui.solution_widget import SolutionWidget


class MainWindow(QDialog):

    def __init__(self):
        super(MainWindow, self).__init__(None)
        self.resize(500, 500)
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.solution_widget = SolutionWidget(self)
        self.layout.addWidget(self.solution_widget)

    def get_solution_widget(self) -> SolutionWidget:
        return self.solution_widget
