import logging
import random

from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from album.core.api.model.task import ILogHandler
from album.core.model.task import Task
from album.runner import album_logging
from album.runner.album_logging import get_active_logger


class Worker(QRunnable):

    class LogHandler(ILogHandler, QObject):
        new_log = pyqtSignal(list)
        task_finished = pyqtSignal()

        def __init__(self):
            QObject.__init__(self)
            ILogHandler.__init__(self)
            self._records = []

        def emit(self, record: logging.LogRecord) -> None:
            self._records.append(record)
            self.new_log.emit(self.records())

        def records(self):
            return self._records

    def __init__(self, method, method_args):
        super().__init__()
        self.task = Task(method, method_args)
        self.task.set_id(random.randint(0, 10000))
        self.handler = Worker.LogHandler()

    def run(self):
        get_active_logger().info(f"starting task {self.task.id()}...")
        logger = album_logging.configure_logging("task" + str(self.task.id()))
        logger.addHandler(self.handler)
        self.task.set_log_handler(self.handler)
        try:
            self.task.method()(**self.task.args())
        except Exception as e:
            logger.error(e)
            # TODO set window to failed
        logger.removeHandler(self.handler)
        album_logging.pop_active_logger()
        get_active_logger().info(f"finished task {self.task.id()}.")
        self.handler.task_finished.emit()
