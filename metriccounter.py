"""A metric counter for time series monitoring."""

import sched
import socket
import sys
import threading
import time

DEFAULT_PUT_FORMAT = 'opentsdb'
try:
    import collectors.lib
    DEFAULT_PUT_FORMAT = 'tcollector'
except ImportError:
    pass

PUT_FORMATS = {
    'opentsdb': 'put %(name)s %(timestamp)s %(value)s %(tag_string)s\n',
    'tcollector': '%(name)s %(timestamp)s %(value)s %(tag_string)s\n',
}

class MetricCounter(object):

    """MetricCounter."""

    # opentsdb's put
    fmt = PUT_FORMATS.get(DEFAULT_PUT_FORMAT)
    tags = None
    tag_string = None

    def __init__(self, name, timespan=15, granularity=1, tags={}, fmt=None):
        self.name = name
        self.timespan = timespan
        self.granularity = granularity
        self.last = 0
        self.cells = [0.0] * (timespan + 1)
        # Allow for overwriting the host tag.
        _tags = {'host': socket.gethostname()}
        _tags.update(tags)
        if fmt:
            self.fmt = fmt
        if DEFAULT_PUT_FORMAT == 'tcollector':
            # tcollector automatically appends the host tag.
            if 'host' in _tags:
                _tags.pop('host')
        self.set_tags(_tags)

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

    def set_tags(self, tags):
        """Set the value of current cells."""
        self.tags = tags
        self.tag_string = " ".join(
            '{}={}'.format(k, v) for k, v in tags.iteritems())

    def get_sum(self):
        """Get the sum of values in the counter."""
        self._refresh()
        return sum(self.cells)

    def flush(self):
        """Flush the counter."""
        for i in range(len(self.cells)):
            self.cells[i] = 0.0

    def dump(self):
        """Dump counter per granularity."""
        self._refresh()
        now = self.now()
        current_cell = self._current_cell()
        cells = self.cells[current_cell+1:] + self.cells[:current_cell]
        for part in range(0, self.timespan, self.granularity):
            value = sum(cells[part: part + self.granularity])
            timestamp = now - self.timespan + part
            sys.stdout.write(
                self.fmt % {
                    'name': self.name,
                    'timestamp': timestamp,
                    'value': value,
                    'tag_string': self.tag_string
                }
            )

    def _refresh(self):
        """Purge outdated cells in the counter."""
        now = self.now()
        current_cell = self._current_cell()
        tdiff = now - self.last
        if tdiff > self.timespan:
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
        """Set an alternative wall clock function."""
        cls.time = timefunc

    @classmethod
    def set_sleep_function(cls, sleepfunc):
        """Set an alternative sleep function."""
        cls.sleep = sleepfunc


class autodump(object):

    """Automatically dump counter records at a constant granularity."""

    def __init__(self, metric_counter):
        self.metric_counter = metric_counter
        self.stopping = False
        self._scheduler = sched.scheduler(StopWatch.time, StopWatch.sleep)

        since_last_dump = metric_counter.now() % metric_counter.timespan
        next_dump_time = (
            metric_counter.now() - since_last_dump + metric_counter.timespan
        )
        self._scheduler.enterabs(next_dump_time, 0, self._dump_reschedule, [])

        self.dumper_thread = threading.Thread(target=self._scheduler.run)

    def _dump_reschedule(self):
        """Reschedule dump action at the next granularity and dump values."""
        if not self.stopping:
            self._scheduler.enterabs(
                self.metric_counter.now() + self.metric_counter.timespan, 0,
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
