"""A rate counter for time series monitoring."""

import sched
import sys
import threading
import time


class RateCounter(object):

    """RateCounter."""

    def __init__(self, name, span_secs=15, interval_secs=1):
        self.name = name
        self.span_secs = span_secs
        self.interval_secs = interval_secs
        self.last = 0
        self.cells = [0.0] * (span_secs + 1)

    def inc(self):
        """Increment the counter by 1"""
        self.add(1)

    def add(self, value):
        """Increment the counter by a value."""
        self._refresh()
        self.cells[self._current_cell()] += value

    def get(self):
        """Get the sum of values in the counter."""
        self._refresh()
        return sum(self.cells)

    def flush(self):
        """Flush the counter."""
        for i in range(len(self.cells)):
            self.cells[i] = 0.0

    def dump(self):
        """Dump counter per interval."""
        self._refresh()
        now = self.now()
        current_cell = self._current_cell()
        cells = self.cells[current_cell+1:] + self.cells[:current_cell]
        for part in range(0, self.span_secs, self.interval_secs):
            value = sum(cells[part: part + self.interval_secs])
            timestamp = now - self.span_secs + part
            sys.stdout.write('{} {} {}\n'.format(self.name, timestamp, value))

    def _refresh(self):
        """Purge outdated cells in the counter."""
        now = self.now()
        current_cell = self._current_cell()
        tdiff = now - self.last
        if tdiff > self.span_secs:
            self.flush()
        elif tdiff:
            for i in range(current_cell - tdiff + 1, current_cell + 1):
                self.cells[i] = 0.0
        self.last = now

    @staticmethod
    def now():
        """Return current timestamp in seconds."""
        return int(time.time())

    def _current_cell(self):
        """Return current cell based on current timestamp."""
        return self.now() % len(self.cells)


class autodump(object):

    """Helper class automatically dump rate counter at an interval."""

    def __init__(self, rate_counter):
        self.rate_counter = rate_counter
        self.stopping = False
        self._scheduler = sched.scheduler(time.time, time.sleep)

        since_last_dump = rate_counter.now() % rate_counter.span_secs
        next_dump_time = (
            rate_counter.now() - since_last_dump + rate_counter.span_secs
        )
        self._scheduler.enterabs(next_dump_time, 0, self._dump_reschedule, [])

        self.dumper_thread = threading.Thread(target=self._scheduler.run)

    def _dump_reschedule(self):
        """Reschedule dump action at the next interval and dump values."""
        if not self.stopping:
            self._scheduler.enterabs(
                self.rate_counter.now() + self.rate_counter.span_secs, 0,
                self._dump_reschedule, []
            )
        self.rate_counter.dump()

    def __enter__(self):
        self.dumper_thread.start()
        return self.rate_counter

    def __exit__(self, ttype, value, traceback):
        self.stopping = True
        self.dumper_thread.join()
        self.stopping = False
        return False
