import logging
import platform
import random
import traceback

from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from album.core.api.model.task import ILogHandler
from album.core.model.task import Task
from album.runner import album_logging
from album.runner.album_logging import get_active_logger, LogLevel


class Worker(QRunnable):

    class LogHandler(ILogHandler, QObject):
        new_log = pyqtSignal(logging.LogRecord)
        task_finished = pyqtSignal()
        task_failed = pyqtSignal()

        def __init__(self):
            QObject.__init__(self)
            ILogHandler.__init__(self)
            self._records = []

        def emit(self, record: logging.LogRecord) -> None:
            self._records.append(record)
            self.new_log.emit(record)

        def records(self):
            return self._records

    def __init__(self, method, method_args):
        super().__init__()
        self.task = Task(method, method_args)
        self.task.set_id(random.randint(0, 10000))
        self.handler = Worker.LogHandler()

    def run(self):
        get_active_logger().debug(f"starting task {self.task.id()}...")
        logger = album_logging.configure_logging("task" + str(self.task.id()), loglevel=LogLevel.INFO)
        logger.addHandler(self.handler)
        self.task.set_log_handler(self.handler)
        try:
            if platform.system() == 'Windows':
                import pythoncom
                pythoncom.CoInitialize()
            self.task.method()(**self.task.args())
            get_active_logger().debug(f"finished task {self.task.id()}.")
            self.handler.task_finished.emit()
        except Exception as e:
            traceback.print_exc()
            logger.error(str(e))
            # TODO set window to failed
        finally:
            if platform.system() == 'Windows':
                pythoncom.CoUninitialize()
            logger.removeHandler(self.handler)
            album_logging.pop_active_logger()
