import unittest

from PyQt5.QtCore import QThreadPool
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from album.runner.album_logging import get_active_logger

from album.gui.solution_window import SolutionWidget
from album.gui.worker import Worker


class TestIntegrationSolutionStatusWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(['-platform', 'offscreen'])

    def test_update_solution_log(self):
        win = SolutionWidget()

        def mock_task_method(name):
            get_active_logger().info("Log1\nLog2\nLog3")
            get_active_logger().info("Log4")

        worker = Worker(mock_task_method, {"name": "bla"})

        worker.handler.new_log.connect(lambda records: win.get_install_widget().update_solution_log(records))

        threadpool = QThreadPool.globalInstance()
        threadpool.start(worker)

        QTest.qWait(1000)

        self.assertEqual("Log1\nLog2\nLog3\nLog4", win.get_install_widget().run_output.toPlainText())

        threadpool.waitForDone()

    def test_update_solution_log_longtext(self):
        win = SolutionWidget()

        longtext1 = ""
        longtext2 = ""
        for i in range(1000):
            longtext1 += f"\nlog1 {i}"
            longtext2 += f"\nlog2 {i}"

        def mock_task_method(name):
            get_active_logger().info(longtext1)
            get_active_logger().info(longtext2)

        worker = Worker(mock_task_method, {"name": "bla"})

        worker.handler.new_log.connect(lambda records: win.get_install_widget().update_solution_log(records))

        threadpool = QThreadPool.globalInstance()
        threadpool.start(worker)

        QTest.qWait(1000)

        self.assertEqual(longtext1 + "\n" + longtext2, win.get_install_widget().run_output.toPlainText())

        # Clean up
        threadpool.waitForDone()
