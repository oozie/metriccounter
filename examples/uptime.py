#!/usr/bin/python

from metriccounter import MetricCounter, autodump, run_every_n_seconds

INTERVAL = 120

if __name__ == "__main__":
    since_boot = MetricCounter('proc.uptime.since_boot', timespan=INTERVAL, granularity=INTERVAL)
    idle = MetricCounter('proc.uptime.idle', timespan=INTERVAL, granularity=INTERVAL)

    def get_uptime():
        with open('/proc/uptime') as proc_uptime:
            since_boot_secs, idle_secs = [float(e) for e in proc_uptime.read().split()]

        idle.set(int(idle_secs))
        since_boot.set(int(since_boot_secs))

    with autodump():
        run_every_n_seconds(INTERVAL, get_uptime)
