import sys
from time import sleep
from unittest.mock import create_autospec

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QProgressBar, \
    QPushButton
from album.api import Album

from album.gui.dialog.checklist_dialog import CheckListDialog
from album.gui.dialog.solution_action_process_thread import SolutionActionProcessThread
from album.gui.dialog.update_solutions_dialog import UpdateSolutionDialog
from album.gui.solution_util import generate_remove_solutions_actions


class UninstallSolutionsFromCatalogDialog(CheckListDialog):
    upgrade_running = pyqtSignal(bool)
    upgradeRunning = pyqtSignal(bool)
    upgradeDone = pyqtSignal()
    availableUpdatesChanged = pyqtSignal(bool)

    def __init__(self, options, album_instance):
        super().__init__(options, "Uninstall solutions from catalogs", "From which catalogs do you want to uninstall all solutions?", "Uninstall solution(s)")
        self.album_instance = album_instance
        self.upgrade_running.connect(lambda enabled: self.set_finished() if not enabled else None)
        self.actionSubmitted.connect(self.upgrade)

    def create_progress_view(self) -> QDialog:
        view = QDialog(self)
        view.setWindowTitle("Uninstalling solutions..")
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

    def upgrade(self, catalog_names):
        actions = generate_remove_solutions_actions(self.album_instance, catalog_names)
        self.solution_actions = actions
        self.current_processed_item = 0
        self.upgrade_running.emit(True)
        dialog = self.create_progress_view()
        self.upgrade_next_item()
        dialog.exec_()

    def upgrade_next_item(self):
        if self.current_processed_item >= len(self.solution_actions):
            self.upgrade_running.emit(False)
            return
        solution_action = self.solution_actions[self.current_processed_item]
        self.current_catalog_label.setText(UpdateSolutionDialog.get_action_text(solution_action))
        self.thread = SolutionActionProcessThread(solution_action, self.album_instance)
        self.thread.processFinished.connect(self.on_update_finished)
        self.thread.processFailed.connect(lambda x: self.upgradeDone.emit())
        self.thread.start()

    def on_update_finished(self, item):
        self.current_processed_item += 1
        self.upgrade_next_item()

    def set_finished(self):
        self.progressbar.setVisible(False)
        self.close_button.setVisible(True)
        self.current_catalog_label.setText("Uninstalling solutions done.")
        self.upgradeDone.emit()


class UpdateProcessThread(QThread):
    processFinished = pyqtSignal(str)

    def __init__(self, item, album_instance: Album):
        super().__init__()
        self.item = item
        self.album_instance = album_instance

    def run(self):
        self.album_instance.upgrade(self.item)
        self.processFinished.emit(self.item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    options = ["Option " + str(i) for i in range(1, 51)]
    album = create_autospec(Album)
    album.upgrade = lambda x: sleep(1)
    dialog = UninstallSolutionsFromCatalogDialog(options, album)
    if dialog.exec_() == QDialog.Accepted:
        all_checked, checked_items = dialog.getCheckedItems()
        print("All choices activated: ", all_checked)
        print("Activated choices: ", checked_items)
    sys.exit(app.exec_())