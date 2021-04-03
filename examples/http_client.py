"""Simple http client example.

Check out crawler.py for more advanced behaviors involving
many concurrent clients.
"""

from diesel import Application, Loop, quickstart, quickstop
from diesel import log
from diesel.protocols.http import HttpClient

def req_loop():
    for path in ['/contact.shtml', '/']:
        with HttpClient('www.opennet.ru', 80) as client:
            headers = {'Host': 'opennet.ru'}
            log.info(str(client.request('GET', path, headers)))
    quickstop()

log = log.name('http-client')
quickstart(req_loop)
