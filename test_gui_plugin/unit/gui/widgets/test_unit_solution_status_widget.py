import unittest
from PyQt5.QtWidgets import QApplication
from album.gui.widgets.solution_status_widget import SolutionStatus


class TestUnitSolutionStatusWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def test__update_solution_log(self):
        solution_status = SolutionStatus(None)
        # Simulate initial log records as dictionaries
        initial_records = [
            {"msg": "Log 1", "asctime": "2021-01-01"},
            {"msg": "Log 2", "asctime": "2021-01-02"},
        ]

        # Initially, no logs should be displayed
        self.assertEqual(solution_status.run_output.toPlainText(), "")

        # Update log and check
        solution_status.update_solution_log(initial_records)
        self.assertEqual(solution_status.run_output.toPlainText(), "Log 1\nLog 2")

        # Simulate new log records, partially overlapping with initial_records
        new_records = [
            {"msg": "Log 2", "asctime": "2021-01-02"},
            {"msg": "Log 3", "asctime": "2021-01-03"},
        ]

        # Update log with new records and check for duplicates
        solution_status.update_solution_log(new_records)
        self.assertEqual(solution_status.run_output.toPlainText(), "Log 1\nLog 2\nLog 3")

        # Simulate another new log, should not create duplicates
        another_new_record = [
            {"msg": "Log 3", "asctime": "2021-01-03"},
            {"msg": "Log 4", "asctime": "2021-01-04"},
        ]

        solution_status.update_solution_log(another_new_record)
        self.assertEqual(solution_status.run_output.toPlainText(), "Log 1\nLog 2\nLog 3\nLog 4")
