# vim:ts=4:sw=4:expandtab
"""Example of deferring blocking calls to threads"""

import time
from functools import partial

from diesel import log, thread, quickstart


def blocker(taskid, sleep_time):
    while True:
        def f():
            time.sleep(sleep_time)
        thread(f)
        log.info('yo! {0} from {1} task', time.time(), taskid)


quickstart(partial(blocker, 'fast', 1), partial(blocker, 'slow', 5))
