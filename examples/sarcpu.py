#!/usr/bin/python

from subprocess import Popen, PIPE
from metriccounter import MetricCounter, autodump

CPU_METRIC = 'sar.cpu.util'
UTIL_TYPES = ['user', 'nice', 'system', 'iowait', 'steal', 'idle']

GRANULARITY = 1

if __name__ == "__main__":

    counters = []
    for utype in UTIL_TYPES:
        counters.append(
            MetricCounter(CPU_METRIC,
                timespan=GRANULARITY, 
                granularity=GRANULARITY,
                tags={'type': utype}
            )
        )

    # Poll sar at a regular interval.
    sar = Popen('sar %s' % GRANULARITY, shell=True, stdout=PIPE)
    # Discard the first three lines
    for i in range(3):
        sar.stdout.readline()
    
    with autodump():
        while True:
            line = sar.stdout.readline()
            no_time_line = line[12:].strip()  # Strip timestamp.
            # Ignore first column.
            measurements = [float(m) for m in no_time_line.split()[1:]]
            for i in range(len(counters)):
                counters[i].set(measurements[i])
