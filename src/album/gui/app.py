from PyQt5.QtCore import pyqtSignal, QThreadPool, QObject
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, \
    QProgressBar, QLineEdit, QCheckBox, QHBoxLayout
from album.api import Album

from album.gui.collection_window import CollectionWindow
from album.gui.dialog.about_dialog import AboutDialog
from album.gui.dialog.solutions_action_dialog import SolutionsActionDialog
from album.gui.dialog.uninstall_solutions_from_catalog_dialog import UninstallSolutionsFromCatalogDialog
from album.gui.dialog.update_album_dialog import UpdateAlbumDialog
from album.gui.dialog.update_catalog_dialog import UpdateCatalogDialog
from album.gui.dialog.update_solutions_dialog import UpdateSolutionDialog
from album.gui.solution_util import generate_install_all_actions
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
            win.uninstall_solutions.connect(lambda sol: self.uninstall_solutions(sol))
            win.remove_catalog.connect(self.remove_catalog)
            win.add_new_catalog.connect(self.add_catalog)
            win.open_about.connect(self.show_about_dialog)
            win.update_album.connect(self.update_album_dialog)
            win.update_solution_dialog.connect(self.choose_update_solutions)
            win.batch_uninstall_dialog.connect(self.choose_batch_uninstall_catalogs)
            win.update_catalog_dialog.connect(self.choose_update_catalogs)
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
            solution_data = self.get_database_entry(solution)
            self._install(win, solution, solution_data)
        except LookupError:
            display_error("Cannot find solution %s." % solution)
        self.open_windows.append(win)
        win.show()

    def get_database_entry(self, solution):
        return self.get_unloaded_resolve_result(solution).database_entry()

    def get_unloaded_resolve_result(self, solution):
        return self.album_instance._controller.collection_manager()._resolve(solution)

    def uninstall_solution(self, solution):
        win = SolutionWidget()
        try:
            solution_data = self.get_database_entry(solution)
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

    def uninstall_solutions(self, actions):
        dialog = SolutionsActionDialog(self.album_instance, actions, "Uninstall solution versions", "Would you like to uninstall the following versions of this solution?", "Uninstall")
        dialog.upgradeDone.connect(self.collection_changed)
        dialog.exec_()

    def _widget_finished(self, widget):
        widget.set_solution_finished()
        self.collection_changed.emit()

    def remove_catalog(self, catalog):
        if display_confirmation("Do you really want to remove catalog %s (%s)?" % (catalog["name"], catalog["src"])):
            try:
                worker = Worker(self.album_instance.remove_catalog_by_name, {"catalog_src": catalog["name"]})
                worker.handler.task_finished.connect(self.collection_changed)
                worker.handler.task_finished.connect(self.catalog_removed)
                worker.handler.new_log.connect(lambda record: self._check_log_for_error(record))
                self.threadpool.start(worker)
            except RuntimeError as e:
                display_error(str(e))

    def add_catalog(self, parent):
        dialog = QDialog(parent)
        layout = QVBoxLayout(dialog)
        input_label = QLabel('Enter the catalog path or URL:')
        line_edit = QLineEdit()
        checkbox = QCheckBox('Install all solutions from catalog')

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(dialog.accept)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(dialog.reject)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addWidget(input_label)
        layout.addWidget(line_edit)
        layout.addWidget(checkbox)
        layout.addLayout(btn_layout)
        if dialog.exec_() == QDialog.Accepted:
            progress_dialog = QDialog(parent)
            layout = QVBoxLayout()
            close_button = QPushButton("Close")
            close_button.setVisible(False)
            close_button.clicked.connect(progress_dialog.close)
            catalog_src = line_edit.text().strip()
            progress_label = QLabel("Adding catalog %s.." % catalog_src)
            layout.addWidget(progress_label)
            progressbar = QProgressBar()
            progressbar.setRange(0, 0)
            layout.addWidget(progressbar)
            layout.addWidget(close_button)
            progress_dialog.setLayout(layout)
            try:

                # Create worker
                worker = Worker(self.album_instance.add_catalog, {"catalog_src": catalog_src})

                worker.handler.task_finished.connect(self.collection_changed)
                worker.handler.task_finished.connect(lambda: progressbar.setVisible(False))
                worker.handler.task_finished.connect(lambda: close_button.setVisible(True))
                if checkbox.isChecked():
                    worker.handler.task_finished.connect(lambda: progress_dialog.close())
                    worker.handler.task_finished.connect(lambda: self.install_all_solutions_from_catalog(catalog_src))
                else:
                    worker.handler.task_finished.connect(lambda: progress_label.setText("Successfully added catalog %s." % catalog_src))

                # Start the worker
                self.threadpool.start(worker)
                progress_dialog.exec_()

            except Exception as e:
                self.album_instance.remove_catalog_by_src(catalog_src)
                display_error(str(e))
                progress_dialog.close()  # Close the progress dialog in case of error

    def install_all_solutions_from_catalog(self, catalog_src):
        install_actions = generate_install_all_actions(self.album_instance, catalog_src)
        dialog = SolutionsActionDialog(self.album_instance, install_actions, "Install all solutions from catalog",
                                       "Successfully added catalog %s. Would you like to install the following solutions from the catalog?" % catalog_src,
                                       "Install")
        dialog.upgradeDone.connect(self.collection_changed)
        dialog.exec_()

    def show_about_dialog(self, parent):
        dialog = AboutDialog(parent)
        dialog.exec_()

    def update_album_dialog(self, parent):
        dialog = UpdateAlbumDialog(parent, self.album_instance.configuration().base_cache_path())
        dialog.exec_()

    def choose_update_catalogs(self, options):
        dialog = UpdateCatalogDialog(options, self.album_instance)
        dialog.upgradeDone.connect(self.collection_changed)
        dialog.exec_()

    def choose_batch_uninstall_catalogs(self, options):
        dialog = UninstallSolutionsFromCatalogDialog(options, self.album_instance)
        dialog.upgradeDone.connect(self.collection_changed)
        dialog.exec_()

    def choose_update_solutions(self):
        dialog = UpdateSolutionDialog(self.album_instance)
        dialog.upgradeDone.connect(self.collection_changed)
        dialog.exec_()

    def catalog_removed(self):
        display_info("Action complete", "Successfully removed catalog.")

    def _install_if_needed(self, win, solution):
        solution_data = self.get_database_entry(solution)
        win.set_show_solution(solution_data)
        if not self.is_installed(solution):
            win.get_pre_install_widget().install_solution.connect(lambda: self._install(win, solution, solution_data))
            win.show_pre_install()
        else:
            self._show_pre_run(win, solution, solution_data)

    def is_installed(self, solution):
        resolve_result = self.get_unloaded_resolve_result(solution)
        return self.album_instance._controller.solutions().is_installed(
            resolve_result.catalog(), resolve_result.coordinates()
        )

    def _install(self, win, solution, solution_data):
        win.set_show_solution(solution_data)
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
                win.get_run_widget().continue_signal.connect(lambda: self.restart_run(win))
                worker = Worker(self.album_instance.run, {"solution_to_resolve": solution,
                                                          "argv": self._construct_args(solution, values)})
                worker.handler.task_finished.connect(lambda: win.get_run_widget().set_solution_finished())
                self.ongoing_processes[win] = worker
                worker.handler.new_log.connect(lambda records: win.get_run_widget().update_solution_log(records))
                self.threadpool.start(worker)

    def restart_run(self, win):
        win.get_run_widget().run_output.clear()
        win.get_run_widget().set_solution_unfinished()
        return win.show_pre_run()

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
    def _check_log_for_error(record):
        if record.levelname == "ERROR":
            display_error(str(record.msg))


if __name__ == '__main__':
    album = Album.Builder().build()
    album.load_or_create_collection()
    gui = AlbumGUI(album)
    gui.launch()
    # gui.launch(solution="template-python")
