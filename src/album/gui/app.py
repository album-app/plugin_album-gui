from PyQt5.QtCore import pyqtSignal, QThreadPool, QObject
from PyQt5.QtWidgets import QApplication, QInputDialog
from album.api import Album

from album.gui.collection_window import CollectionWindow
from album.gui.solution_window import SolutionWidget
from album.gui.widgets.util import display_error, display_confirmation, display_info
from album.gui.worker import Worker


class AlbumGUI(QObject):
    collection_changed = pyqtSignal()

    def __init__(self, album_instance):
        super().__init__()
        self.app = QApplication([])
        self.album_instance: Album = album_instance
        self.threadpool = QThreadPool()
        self.open_windows = []
        self.ongoing_processes = {}

    def launch(self, solution=None):
        if solution:
            win = SolutionWidget()
            try:
                self._install_if_needed(win, solution)
            except LookupError:
                display_error("Cannot find solution %s." % solution)
                return
        else:
            win = CollectionWindow(self.album_instance)
            win.show_solution.connect(lambda sol: self.launch_solution(sol))
            win.install_solution.connect(lambda sol: self.install_solution(sol))
            win.uninstall_solution.connect(lambda sol: self.uninstall_solution(sol))
            win.remove_catalog.connect(self.remove_catalog)
            win.add_new_catalog.connect(self.add_catalog)
            win.update_catalogs.connect(self.update_catalogs)
            win.update_all_catalogs.connect(self.update_all_catalogs)
            self.collection_changed.connect(win.update_model)
        win.show()
        self.app.exec()

    def launch_solution(self, solution):
        win = SolutionWidget()
        try:
            self._install_if_needed(win, solution)
        except LookupError:
            display_error("Cannot find solution %s." % solution)
        self.open_windows.append(win)
        win.show()

    def install_solution(self, solution):
        win = SolutionWidget()
        try:
            solution_data = self.album_instance.resolve(solution).database_entry()
            self._install(win, solution, solution_data)
        except LookupError:
            display_error("Cannot find solution %s." % solution)
        self.open_windows.append(win)
        win.show()

    def uninstall_solution(self, solution):
        win = SolutionWidget()
        try:
            solution_data = self.album_instance.resolve(solution).database_entry()
            win.set_show_solution(solution_data)
            if not self.album_instance.is_installed(solution):
                return
            else:
                win.get_uninstall_widget().continue_signal.connect(lambda: win.close())
                win.show_uninstall()
                worker = Worker(self.album_instance.uninstall, {"solution_to_resolve": solution})
                worker.handler.task_finished.connect(lambda: self._widget_finished(win.get_uninstall_widget()))
                self.ongoing_processes[win] = worker
                worker.handler.new_log.connect(lambda records: win.get_uninstall_widget().update_solution_log(records))
                self.threadpool.start(worker)
        except LookupError:
            display_error("Cannot find solution %s." % solution)
        self.open_windows.append(win)
        win.show()

    def _widget_finished(self, widget):
        widget.set_solution_finished()
        self.collection_changed.emit()

    def remove_catalog(self, catalog):
        if display_confirmation("Do you really want to remove catalog %s (%s)?" % (catalog["name"], catalog["src"])):
            try:
                worker = Worker(self.album_instance.remove_catalog_by_name, {"catalog_src": catalog["name"]})
                worker.handler.task_finished.connect(self.collection_changed)
                worker.handler.task_finished.connect(self.catalog_removed)
                worker.handler.new_log.connect(lambda records: self._check_log_for_error(records))
                self.threadpool.start(worker)
            except RuntimeError as e:
                display_error(str(e))

    def add_catalog(self, parent):
        text, ok = QInputDialog.getText(parent, 'Add catalog', 'Enter the catalog path or URL:')
        if ok:
            try:
                worker = Worker(self.album_instance.add_catalog, {"catalog_src": text})
                worker.handler.task_finished.connect(self.catalog_added)
                worker.handler.task_finished.connect(self.collection_changed)
                self.threadpool.start(worker)
            except Exception as e:
                self.album_instance.remove_catalog_by_src(text)
                display_error(str(e))

    def update_catalogs(self, catalogs):
        for catalog in catalogs:
            try:
                worker = Worker(self.album_instance.update, {"catalog_name": catalog})
                worker.handler.task_finished.connect(lambda: self.catalog_updated(catalog))
                worker.handler.task_finished.connect(self.collection_changed)
                self.threadpool.start(worker)
            except Exception as e:
                display_error(str(e))

    def update_all_catalogs(self):
        try:
            worker = Worker(self.album_instance.update, {"catalog_name": None})
            worker.handler.task_finished.connect(self.all_catalogs_updated)
            worker.handler.task_finished.connect(self.collection_changed)
            self.threadpool.start(worker)
        except Exception as e:
            display_error(str(e))

    def catalog_added(self):
        display_info("Action complete", "Successfully added catalog.")

    def catalog_updated(self, catalog_name):
        display_info("Action complete", "Successfully updated catalog %s." % catalog_name)

    def all_catalogs_updated(self):
        display_info("Action complete", "Successfully updated all catalogs.")

    def catalog_removed(self):
        display_info("Action complete", "Successfully removed catalog.")

    def _install_if_needed(self, win, solution):
        solution_data = self.album_instance.resolve(solution).database_entry()
        win.set_show_solution(solution_data)
        if not self.album_instance.is_installed(solution):
            win.get_pre_install_widget().install_solution.connect(lambda: self._install(win, solution, solution_data))
            win.show_pre_install()
        else:
            self._show_pre_run(win, solution, solution_data)

    def _install(self, win, solution, solution_data):
        win.get_install_widget().continue_signal.connect(lambda: self._show_pre_run(win, solution, solution_data))
        win.show_install()

        worker = Worker(self.album_instance.install, {"solution_to_resolve": solution})
        worker.handler.task_finished.connect(lambda: self._widget_finished(win.get_install_widget()))
        self.ongoing_processes[win] = worker
        worker.handler.new_log.connect(lambda records: win.get_install_widget().update_solution_log(records))
        self.threadpool.start(worker)

    def _cancel_installation(self, win, solution, solution_data):
        self.threadpool.cancel(self.ongoing_processes[win])
        self.ongoing_processes.pop(win)
        win.close()

    def _show_pre_run(self, win, solution, solution_data):
        win.get_pre_run_widget().run_solution.connect(lambda: self._run(win, solution))
        win.get_pre_run_widget().cancel_solution.connect(lambda: win.close())
        win.show_pre_run()
        if "args" in solution_data.setup():
            args = solution_data.setup()["args"]
            win.get_pre_run_widget().add_arguments(args)

    def _setup_album(self, album_instance):
        self.album_instance = album_instance

    def dispose(self):
        self.album_instance = None

    def _cancel(self):
        self.dispose()

    def _run(self, win, solution):
        if win.get_pre_run_widget().check_required_fields():
            if self.album_instance:
                values = win.get_pre_run_widget().get_values()
                win.show_run()
                win.get_run_widget().continue_signal.connect(lambda: win.close())
                worker = Worker(self.album_instance.run, {"solution_to_resolve": solution,
                                                          "argv": self._construct_args(solution, values)})
                worker.handler.task_finished.connect(lambda: win.get_run_widget().set_solution_finished())
                self.ongoing_processes[win] = worker
                worker.handler.new_log.connect(lambda records: win.get_run_widget().update_solution_log(records))
                self.threadpool.start(worker)

    @staticmethod
    def _build_args(args):
        res = []
        for arg in args:
            res.append("--%s" % arg)
            res.append(args[arg])
        return res

    @staticmethod
    def _construct_args(solution, values):
        res = [solution]
        for name in values:
            res.append("--%s" % name)
            res.append(values[name])
        return res

    @staticmethod
    def _check_log_for_error(records):
        last_record = records[len(records) - 1]
        if last_record.levelname == "ERROR":
            display_error(str(last_record.msg))


if __name__ == '__main__':
    album = Album.Builder().build()
    album.load_or_create_collection()
    gui = AlbumGUI(album)
    gui.launch()
    # gui.launch(solution="template-python")
