# metriccounter
This is a Python implementation of a metric counter for recording time series data at up-to 1-second granularity. All examples work out-of-the-box with tcollector and as raw OpenTSDB puts.
## Usage
### with tcollector
`MetricCounter` works best as a so called long-lived collector.
* Consecutive datapoints of the same value will be deduped,
* ingestion delay on the order of minutes,
* To deploy, place collectors under `collectors/0`

### as raw OpenTSDB puts
Little overhead in creating collectors allows for quick prototyping and burstiness/performance analyses, sending data as raw input to OpenTSDB
* stores a lot of datapoints; 
* ingestion delay on the orders of seconds
* To send data to OpenTSDB, pipe the output from your collector to the TSD
```sh
$ python collector.py | nc opentsdb.host.corp 4242
```
## Examples
### Flow metrics (rate counters)
#### authfailures.py
```python
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
```
![](https://raw.githubusercontent.com/oozie/metriccounter/gh-pages/images/authfailures.png)

### Stock metrics
#### ![numprocesses.py](https://github.com/oozie/metriccounter/blob/master/examples/numprocesses.py) - per-second, per-state breakdown of running processes

![](https://raw.githubusercontent.com/oozie/metriccounter/gh-pages/images/numprocesses.png)
