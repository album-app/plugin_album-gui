import logging
import unittest
from unittest.mock import patch

from album.gui.progress_filter import ProgressIntervalFilter
from album.gui.worker import Worker


def _record(message, progress=False):
    record = logging.makeLogRecord({"msg": message, "levelno": logging.INFO, "levelname": "INFO"})
    if progress:
        record.album_progress = True
    return record


class TestUnitWorker(unittest.TestCase):

    @patch("album.gui.progress_filter.time.monotonic", side_effect=[100.0, 110.0, 131.0])
    def test_progress_interval_filter(self, _):
        progress_filter = ProgressIntervalFilter(30)

        passed = [progress_filter.filter(_record(message, progress=True)) for message in ("0%", "50%", "100%")]

        self.assertEqual([True, False, True], passed)
        self.assertTrue(progress_filter.filter(_record("done")))

    def test_log_keeps_one_progress_update_per_interval(self):
        worker = Worker(lambda: None, {})

        for record in (_record("0%", progress=True), _record("1%", progress=True), _record("100%")):
            worker.handler.handle(record)

        self.assertEqual(["0%", "100%"], [record.getMessage() for record in worker.handler.records()])


if __name__ == "__main__":
    unittest.main()
