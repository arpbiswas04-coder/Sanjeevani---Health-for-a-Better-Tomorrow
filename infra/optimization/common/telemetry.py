"""Bounded in-process metrics. No request IDs, paths, patients or model inputs."""
from contextlib import contextmanager
from functools import wraps
import math
from threading import Lock
from time import perf_counter

NAMES = {'http': {'health', 'api', 'other'}, 'prediction': {'inference'},
         'optimizer': {'redistribution', 'transport', 'routing', 'ambulance', 'emergency',
                       'workforce', 'procurement', 'resilience'}}
BUCKETS = (.001, .01, .05, .1, .5, 1, 5, 30)
_lock, _values = Lock(), {}


def observe(kind, name, status, seconds):
    if name not in NAMES.get(kind, ()) or status not in {'success','error','1xx','2xx','3xx','4xx','5xx'}:
        raise ValueError('Unsupported metric labels')
    if not math.isfinite(seconds) or seconds < 0: raise ValueError('Invalid duration')
    with _lock:
        row = _values.setdefault((kind,name,status), [0, 0., [0]*len(BUCKETS)])
        row[0] += 1
        row[1] += seconds
        for i, bound in enumerate(BUCKETS): row[2][i] += int(seconds <= bound)


@contextmanager
def timed(kind, name):
    start, status = perf_counter(), 'success'
    try: yield
    except BaseException:
        status = 'error'
        raise
    finally: observe(kind, name, status, perf_counter()-start)


def measured(kind, name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with timed(kind,name): return function(*args, **kwargs)
        return wrapped
    return decorate


def render():
    lines = ['# TYPE sanjeevani_operation_calls_total counter',
             '# TYPE sanjeevani_operation_duration_seconds histogram']
    with _lock:
        for (kind,name,status), (count,total,buckets) in sorted(_values.items()):
            labels = f'kind="{kind}",name="{name}",status="{status}"'
            lines += [f'sanjeevani_operation_calls_total{{{labels}}} {count}',
                      f'sanjeevani_operation_duration_seconds_count{{{labels}}} {count}',
                      f'sanjeevani_operation_duration_seconds_sum{{{labels}}} {total}',
                      f'sanjeevani_operation_duration_seconds_bucket{{{labels},le="+Inf"}} {count}']
            lines += [f'sanjeevani_operation_duration_seconds_bucket{{{labels},le="{bound}"}} {value}'
                      for bound,value in zip(BUCKETS,buckets)]
    return '\n'.join(lines)+'\n'
