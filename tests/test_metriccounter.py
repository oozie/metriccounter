import unittest
import time
import metriccounter as mc


def stub_factory(max_iterations=100, max_duration=20):

    def time_stub():
        if not hasattr(time_stub, 'elapsed'):
            time_stub.start_time = time.time()
            time_stub.elapsed = 0
            time_stub.rounds = 0

        if time_stub.rounds >= max_iterations:
            raise StopIteration('max_iterations reached')
        elif time_stub.elapsed >= max_duration:
            raise StopIteration('max_duration elapsed')
        time_stub.rounds += 1
        return time_stub.start_time + time_stub.elapsed

    def sleep_stub(duration):
        time_stub.elapsed += duration

    return time_stub, sleep_stub

class TestMetricCounter(unittest.TestCase):

    def setUp(self):
        time_stub, sleep_stub = stub_factory(max_iterations=10)
        mc.StopWatch.set_time_function(time_stub)
        mc.StopWatch.set_sleep_function(sleep_stub)

    def test_traverse_interface(self):
        counter = mc.MetricCounter('interface_test', timespan=5, granularity=1)
        counter.add(1)
        counter.inc()
        counter.dump()

    def test_run_every_n_seconds(self):
        time_stub, sleep_stub = stub_factory(max_duration=10)
        mc.StopWatch.set_time_function(time_stub)
        mc.StopWatch.set_sleep_function(sleep_stub)

        counter = mc.MetricCounter('test', timespan=100, granularity=1)

        def increase_counter():
            counter.inc()
            mc.StopWatch.sleep(4)

        with self.assertRaises(StopIteration) as ctx_mgr:
            mc.run_every_n_seconds(1, increase_counter)
        self.assertEqual(3, counter.get_sum())
