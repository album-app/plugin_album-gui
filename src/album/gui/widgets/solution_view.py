from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QListView, QMenu

from album.gui.solution_util import full_coordinates, installed, get_uninstall_actions_for_version


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

            versions = item.action.versions

            newest_version = versions[len(versions) - 1]
            if not installed(newest_version):
                install_action = menu.addAction("Install newest version")
                install_action.triggered.connect(
                    lambda b: self.collection_widget.install_solution.emit(full_coordinates(newest_version, item.action.catalog)))

            uninstall_old_versions_actions = get_uninstall_actions_for_version(self.collection_widget.album_instance, versions, item.action.catalog, exclude_newest=True)
            if len(uninstall_old_versions_actions) > 0:
                uninstall_old_action = menu.addAction("Uninstall old versions")
                uninstall_old_action.triggered.connect(lambda b: self.collection_widget.uninstall_solutions.emit(uninstall_old_versions_actions))

            uninstall_all_versions_actions = get_uninstall_actions_for_version(self.collection_widget.album_instance, versions, item.action.catalog, exclude_newest=False)
            if len(uninstall_all_versions_actions) > 0:
                uninstall_action = menu.addAction("Uninstall all versions")
                uninstall_action.triggered.connect(lambda b: self.collection_widget.uninstall_solutions.emit(uninstall_all_versions_actions))
            menu.exec_(e.globalPos())
