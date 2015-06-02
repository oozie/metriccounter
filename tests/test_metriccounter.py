import unittest
import time
import metriccounter as mc


class DevNull(object):
    @staticmethod
    def write(*args, **kwargs):
        pass

    @staticmethod
    def flush(*args, **kwargs):
        pass


def time_stub_factory(max_iterations=100, max_duration=20):

    def time_stub():

        if time_stub.rounds >= max_iterations:
            raise StopIteration('max_iterations reached')
        time_stub.rounds += 1
        return time_stub.start_time + time_stub.elapsed

    time_stub.start_time = time.time()
    time_stub.elapsed = 0
    time_stub.rounds = 0

    def sleep_stub(duration):
        if time_stub.elapsed >= max_duration:
            raise StopIteration('max_duration elapsed: %s' % time_stub.elapsed)
        time_stub.elapsed += duration

    return time_stub, sleep_stub


class TestMetricCounter(unittest.TestCase):

    def setUp(self):
        time_stub, sleep_stub = time_stub_factory(max_iterations=100)
        mc.StopWatch.set_time_function(time_stub)
        mc.StopWatch.set_sleep_function(sleep_stub)

    def test_traverse_interface(self):
        counter = mc.MetricCounter('interface_test', timespan=5, granularity=1,
                                   stream=DevNull())
        counter.add(1)
        counter.inc()
        counter.summarize(sum)
        counter.dump()

    def test_run_every_n_seconds(self):
        time_stub, sleep_stub = time_stub_factory(max_duration=10)
        mc.StopWatch.set_time_function(time_stub)
        mc.StopWatch.set_sleep_function(sleep_stub)

        counter = mc.MetricCounter('test', timespan=100, granularity=1)

        def increase_counter():
            counter.inc()
            mc.StopWatch.sleep(4)

        with self.assertRaises(StopIteration):
            mc.run_every_n_seconds(1, increase_counter)
        self.assertEqual(3, counter.summarize(sum))

    def test_summary_stats(self):
        counter = mc.MetricCounter('test_summary', timespan=20, granularity=1,
                                   stream=DevNull())

        for i in range(10):
            counter.set(i)
            mc.StopWatch.sleep(1)

        counter.dump()
        self.assertEqual(45, counter.summarize(sum))
        self.assertEqual(9, counter.summarize(max))
        self.assertEqual(0, counter.summarize(min))