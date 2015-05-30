#!/usr/bin/python

import os
from metriccounter import MetricCounter, autodump, run_every_n_seconds

PROCESS_STATES = ['running', 'sleeping', 'dead', 'zombie',
    'tracing_stop', 'disk_sleep', 'stopped']

def get_state(pid):
    with open('/proc/%s/status' % pid) as status:
        status.readline()
        state = status.readline()
    return state[10:state.index(')')].replace(' ', '_')

if __name__ == "__main__":
    state_counters = {}
    for state in PROCESS_STATES:
        state_counters[state] = MetricCounter('proc.num_processes',
            tags={'state': state})

    unknown_counter = MetricCounter('proc.num_processes', tags={'state': 'unknown'})
    def count_procs():
        """Count number of running processes."""
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                try:
                    state_counters.get(get_state(pid), unknown_counter).inc()
                except:
                    pass

    with autodump():
        run_every_n_seconds(1, count_procs)
