from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from album.api import Album
from album.core.model.task import Task

from album.gui.main_window import MainWindow
from album.gui.pre_run_solution_widget import PreRunSolutionWidget
from album.gui.run_solution_widget import RunSolutionWidget
from album.gui.solution_widget import SolutionWidget
from album.gui.util import display_error


class AlbumGUI:
    def __init__(self, album_instance, task_manager):
        self.app = QApplication([])
        self.album_instance: Album = album_instance
        self.task_manager = task_manager
        self.solution = None
        self.solution_data = None
        self.win = None

    def launch(self):
        pass

    def launch_solution(self, solution):
        self._setup_solution(solution)
        self.win = MainWindow()
        self.solution_data = self.album_instance.resolve(self.solution).database_entry()
        try:
            self._install_if_needed()
        except LookupError:
            display_error("Cannot find solution %s." % self.solution)
            return
        self.app.exec_()

    def _install_if_needed(self):

        if not self.album_instance.is_installed(self.solution):
            self.win.get_solution_widget().get_pre_install_widget().install_solution.connect(lambda: self._install())
            self.win.get_solution_widget().get_pre_install_widget().cancel_solution.connect(lambda: self._cancel())
            self.win.get_solution_widget().show_pre_install(self.solution_data)
            self.win.show()
        else:
            self._show_pre_run()
            self.win.show()

    def _install(self):
        self.win.get_solution_widget().get_install_widget().continue_after_install.connect(lambda: self._show_pre_run())
        self.win.get_solution_widget().show_install(self.solution_data)
        self.timer = QTimer()
        task = Task()
        task._method = self.album_instance.install
        task._args = (self.solution,)
        res = self.task_manager.register_task(task)
        timer_lambda = lambda: self._check_status(res, self.timer,
                                  self.win.get_solution_widget().get_install_widget().update_solution_log,
                                  self.win.get_solution_widget().get_install_widget().set_solution_finished,
                                  self.win.get_solution_widget().get_install_widget().set_solution_failed)
        self.timer.timeout.connect(timer_lambda)
        self.timer.start(1000)
        self.task_manager.finish_tasks()

    def _show_pre_run(self):
        self.win.get_solution_widget().get_pre_run_widget().run_solution.connect(lambda: self._run())
        self.win.get_solution_widget().get_pre_run_widget().cancel_solution.connect(lambda: self._cancel())
        self.win.get_solution_widget().show_pre_run(self.solution_data)
        if "args" in self.solution_data.setup():
            args = self.solution_data.setup()["args"]
            for arg in args:
                self.win.get_solution_widget().get_pre_run_widget().add_argument(arg)

    def _setup_album(self, album_instance):
        self.album_instance = album_instance

    def dispose(self):
        self.album_instance = None
        if self.win:
            self.win.close()

    def _cancel(self):
        self.dispose()

    def _run(self):
        if self.win.get_solution_widget().get_pre_run_widget().check_required_fields():
            if self.album_instance:
                values = self.win.get_solution_widget().get_pre_run_widget().get_values()
                self.win.get_solution_widget().show_run(self.solution_data)
                self.timer = QTimer()
                task = Task()
                task._method = self.album_instance.run
                task._args = (self.solution, self._construct_args(self.solution, values))
                res = self.task_manager.register_task(task)
                timer_lambda = lambda: self._check_status(res, self.timer,
                                          self.win.get_solution_widget().get_run_widget().update_solution_log,
                                          self.win.get_solution_widget().get_run_widget().set_solution_finished,
                                          self.win.get_solution_widget().get_run_widget().set_solution_failed)
                self.timer.timeout.connect(timer_lambda)
                self.timer.start(1000)

    def _check_status(self, id, rt, records_callback, finished_callback, failed_callback):
        res = self.task_manager.get_status(self.task_manager.get_task(id))
        if "records" in res:
            records = res["records"]
            records_callback(records)
            status = str(res["status"]).lower()
            if status == "finished":
                finished_callback()
                rt.stop()
            if status == "failed":
                failed_callback()
                rt.stop()

    def _setup_solution(self, solution):
        self.solution = solution

    @staticmethod
    def _build_args(args):
        res = []
        for arg in args:
            res.append("--%s" % arg)
            res.append(args[arg])
        return res

    def is_closed(self):
        if self.win:
            return not self.win.isVisible()
        return True

    def _construct_args(self, solution, values):
        res = [solution]
        for name in values:
            res.append("--%s" % name)
            res.append(values[name])
        return res
