from PyQt5.QtCore import QThread, pyqtSignal
from album.api import Album

from album.gui.dialog.update_action_item import UpdateActionItem, UpdateAction
from album.gui.solution_util import full_coordinates
from album.gui.widgets.util import display_error


class SolutionActionProcessThread(QThread):
    processFinished = pyqtSignal(UpdateActionItem)
    processFailed = pyqtSignal(UpdateActionItem)

    def __init__(self, item, album_instance: Album):
        super().__init__()
        self.item = item
        self.album_instance = album_instance

    def run(self):
        try:
            if self.item.update_action == UpdateAction.INSTALL:
                self.album_instance.install(full_coordinates(self.item.solution, self.item.catalog))
            if self.item.update_action == UpdateAction.UNINSTALL:
                self.album_instance.uninstall(full_coordinates(self.item.solution, self.item.catalog))
            self.processFinished.emit(self.item)
        except Exception as e:
            print(f"An error occurred: {e}")
            display_error(f"An error occurred: {e}")
            self.processFailed.emit(self.item)
