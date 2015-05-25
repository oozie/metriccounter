"""A metric counter for time series monitoring."""

import sched
import sys
import threading
import time


class MetricCounter(object):

    """MetricCounter."""

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

    def set(self, value):
        """Set the value of current cells."""
        self._refresh()
        self.cells[self._current_cell()] = value

    def get_sum(self):
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


class StopWatch(object):

    """A basic timer/stopwatch class for use with the 'with' statement.

    Usage:

        with StopWatch() as timer:
            do_stuff()
        print timer.duration  # <-- Duration of the do_stuff() activity
    """

    sleep = time.sleep
    time = time.time

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = self.time()
        return self

    def __exit__(self, ttype, value, traceback):
        self.end_time = self.time()
        self.duration = self.end_time - self.start_time

    @classmethod
    def set_time_function(cls, timefunc):
        cls.time = timefunc

    @classmethod
    def set_sleep_function(cls, sleepfunc):
        cls.sleep = sleepfunc


class autodump(object):

    """Automatically dump counter records at a constant interval."""

    def __init__(self, metric_counter):
        self.metric_counter = metric_counter
        self.stopping = False
        self._scheduler = sched.scheduler(StopWatch.time, StopWatch.sleep)

        since_last_dump = metric_counter.now() % metric_counter.span_secs
        next_dump_time = (
            metric_counter.now() - since_last_dump + metric_counter.span_secs
        )
        self._scheduler.enterabs(next_dump_time, 0, self._dump_reschedule, [])

        self.dumper_thread = threading.Thread(target=self._scheduler.run)

    def _dump_reschedule(self):
        """Reschedule dump action at the next interval and dump values."""
        if not self.stopping:
            self._scheduler.enterabs(
                self.metric_counter.now() + self.metric_counter.span_secs, 0,
                self._dump_reschedule, []
            )
        self.metric_counter.dump()

    def __enter__(self):
        """Start auto-dumping on entering 'when' context."""
        self.dumper_thread.start()
        return self.metric_counter

    def __exit__(self, ttype, value, traceback):
        """Cleanup on leaving 'when' context."""
        self.stopping = True
        self.dumper_thread.join()
        self.stopping = False
        return False


def _get_next_run_time(interval):
    """Get next run time."""
    next_time = StopWatch.time()
    while True:
        next_time += interval
        yield next_time

def run_every_n_seconds(interval, counter, func, args=[], kwargs={}):
    """Run a function at an even interval."""
    next_run_time_generator = _get_next_run_time(interval)
    for next_time_to_run in next_run_time_generator:
        counter.set(func(*args, **kwargs))
        # Fast forward if func run exceeded the duration of the interval.
        while next_time_to_run < StopWatch.time():
            next_time_to_run = _get_next_run_time(interval)
        StopWatch.sleep(next_time_to_run - StopWatch.time())