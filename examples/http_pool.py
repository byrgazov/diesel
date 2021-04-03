
import sys
import time
import functools

from diesel import quickstart, quickstop
from diesel.protocols.http.pool import request

def f():
    t1 = time.time()
    print('-', request("http://opennet.ru/missing"), 'is missing?')
    t2 = time.time()
    print('-', request("http://opennet.ru/missing"), 'is missing?')
    t3 = time.time()
    print('-', request("http://opennet.ru/missing"), 'is missing?')
    t4 = time.time()
    print('-', request("http://opennet.ru/"), 'is found?')
    t5 = time.time()

    print('First request should (probably) have been longer (tcp handshake) than subsequent 3 requests:')

    for x, y in zip([t1, t2, t3, t4], [t2, t3, t4, t5]):
        print('- {:.4f}'.format(y - x))

    quickstop()

quickstart(f)
