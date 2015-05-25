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
* To send data to OpenTSDB
```sh
$ python collector.py | nc opentsdb.host 4242
```
## Examples
### Flow metrics (rate counters)
#### TBD
### Stock metrics
#### numprocesses.py
```python
#!/usr/bin/python

# Count number of running processes.
import os
from metriccounter import MetricCounter, autodump, run_every_n_seconds

def count_procs():
    return len([pid for pid in os.listdir('/proc') if pid.isdigit()])

if __name__ == "__main__":
    process_counter = MetricCounter(
        'proc.num_processes',
        timespan=5,    # Hold a total of 5 seconds.
        granularity=1, # Report data at a single-second granularity.
    )
    with autodump(process_counter) as numproc_counter:
        run_every_n_seconds(1, numproc_counter, count_procs)
```
* tcollector (red line)
* raw opentsdb put (green line)
![](https://raw.githubusercontent.com/oozie/metriccounter/gh-pages/images/numprocesses.png)
