import sys
from copy import deepcopy
from unittest.mock import create_autospec

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QProgressBar, \
    QPushButton
from album.api import Album

from album.gui.dialog.checklist_table_dialog import CheckListTableDialog
from album.gui.dialog.solution_action_process_thread import SolutionActionProcessThread
from album.gui.dialog.update_action_item import UpdateAction
from album.gui.solution_util import group_solutions_by_version, full_coordinates, generate_update_actions


class SolutionsActionDialog(CheckListTableDialog):
    upgrade_running = pyqtSignal(bool)
    upgradeRunning = pyqtSignal(bool)
    upgradeDone = pyqtSignal()
    availableUpdatesChanged = pyqtSignal(bool)

    def __init__(self, album_instance, solution_actions, title, question, submit_text):
        super().__init__(solution_actions, title, question, submit_text)
        self.album_instance: Album = album_instance
        self.resize(600, 400)
        self.upgrade_running.connect(lambda enabled: self.set_finished() if not enabled else None)
        self.actionSubmitted.connect(self.upgrade)

    @staticmethod
    def _get_solution_options(index):
        actions = []
        catalogs = []
        for catalog in index["catalogs"]:
            catalog = deepcopy(catalog)
            catalog["solutions"] = group_solutions_by_version(catalog)
            catalogs.append(catalog)
        generate_update_actions(catalogs, actions)
        return actions

    def create_progress_view(self) -> QDialog:
        view = QDialog(self)
        view.setWindowTitle("Running solution actions..")
        layout = QVBoxLayout()
        self.current_catalog_label = QLabel()
        self.close_button = QPushButton("Close")
        self.close_button.setVisible(False)
        self.close_button.clicked.connect(view.close)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.current_catalog_label)
        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 0)
        layout.addWidget(self.progressbar)
        layout.addWidget(self.close_button)
        view.setLayout(layout)
        return view

    def upgrade(self, update_items):
        self.solutions_with_actions = update_items
        self.current_processed_item = 0
        self.upgrade_running.emit(True)
        dialog = self.create_progress_view()
        self.upgrade_next_item()
        dialog.exec_()

    def upgrade_next_item(self):
        if self.current_processed_item >= len(self.solutions_with_actions):
            self.upgrade_running.emit(False)
            return
        solution_action = self.solutions_with_actions[self.current_processed_item]
        self.current_catalog_label.setText(self._get_action_text(solution_action))
        self.thread = SolutionActionProcessThread(solution_action, self.album_instance)
        self.thread.processFinished.connect(self.on_update_finished)
        self.thread.processFailed.connect(self.on_update_finished)
        self.thread.start()

    @staticmethod
    def _get_action_text(solution_action):
        action_str = ""
        if solution_action.update_action == UpdateAction.INSTALL:
            action_str = "Installing"
        if solution_action.update_action == UpdateAction.UNINSTALL:
            action_str = "Uninstalling"
        return "%s %s" % (action_str, full_coordinates(solution_action.solution, solution_action.catalog))

    def on_update_finished(self, item):
        self.current_processed_item += 1
        self.upgrade_next_item()

    def set_finished(self):
        self.progressbar.setVisible(False)
        self.close_button.setVisible(True)
        self.current_catalog_label.setText("Actions completed.")
        self.upgradeDone.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    album = create_autospec(Album)
    # album.upgrade = lambda x: sleep(1)
    # album.get_index_as_dict.return_value = TestInteractiveGUI._mock_index_dict_updates()
    dialog = SolutionsActionDialog(album, [], "title", "question?", "submit")
    if dialog.exec_() == QDialog.Accepted:
        checked_items = dialog.getCheckedItems()
        print("Activated choices: ", checked_items)
    sys.exit(app.exec_())