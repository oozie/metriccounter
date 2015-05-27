#!/usr/bin/python

import os
from metriccounter import MetricCounter, autodump, run_every_n_seconds

if __name__ == "__main__":
    process_counter = MetricCounter(
        'proc.num_processes',
        timespan=5,    # Hold a total of 5 seconds.
        granularity=1, # Report data at a single-second granularity.
    )

    def count_procs():
        """Count number of running processes."""
        process_counter.set(
            len([pid for pid in os.listdir('/proc') if pid.isdigit()])
        )

    with autodump():
        run_every_n_seconds(1, count_procs)
