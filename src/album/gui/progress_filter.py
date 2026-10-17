import logging
import time

# album-environments gives the log record of a line a solution redraws, like a progress bar
# of tqdm, the attribute album_progress, up to ten times per second. The log of a running solution
# shows one of them per PROGRESS_LOG_INTERVAL seconds; the final state of the bar is a normal
# line. album 1.0 has the same filter in album.core.utils.core_logging, album 0.12 has none.
PROGRESS_LOG_INTERVAL = 30


class ProgressIntervalFilter(logging.Filter):
    """Let a progress update pass at most once per interval, other records always."""

    def __init__(self, interval: float = PROGRESS_LOG_INTERVAL):
        super().__init__()
        self.interval = interval
        self.last_progress = float("-inf")

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "album_progress", False):
            return True
        now = time.monotonic()
        if now - self.last_progress < self.interval:
            return False
        self.last_progress = now
        return True
