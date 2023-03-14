from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QListView, QMenu


class SolutionView(QListView):

    def __init__(self, collection_widget):
        super().__init__()
        self.collection_widget = collection_widget
        self.setModel(self.collection_widget.proxy)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.select_first_item()

    def select_first_item(self):
        index = self.collection_widget.proxy.index(0, 0)
        self.setCurrentIndex(index)
        self.scrollTo(index)

    def contextMenuEvent(self, e: QContextMenuEvent):
        if self.selectionModel().selection().indexes():
            source_index = self.collection_widget.proxy.mapToSource(self.selectedIndexes()[0])
            item = self.collection_widget.search_model.item(source_index.row(), 0)
            menu = QMenu(self)
            if item.action.solution["internal"]["installed"]:
                uninstall_action = menu.addAction("Uninstall")
                uninstall_action.triggered.connect(
                    lambda b: self.collection_widget.uninstall_solution.emit(item.solution_coordinates))
            else:
                install_action = menu.addAction("Install")
                install_action.triggered.connect(
                    lambda b: self.collection_widget.install_solution.emit(item.solution_coordinates))
            menu.exec_(e.globalPos())
