#!/usr/bin/python
from subprocess import Popen, PIPE
from metriccounter import MetricCounter, autodump

if __name__ == "__main__":
    auth_fail_counter = MetricCounter(
        'auth.failures',
        timespan=10,    # Hold a total of 10 seconds.
        granularity=1,  # Report data at a single-second granularity.
    )

    authlog_tail = Popen(
        "tail -f /var/log/auth.log|stdbuf -o0 grep 'authentication failure'",
        shell=True, stdout=PIPE)

    with autodump(auth_fail_counter):
        while authlog_tail.stdout.readline():
            auth_fail_counter.inc()
