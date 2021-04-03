"""Simple echo server.

$ python3 echo.py
$ nc -C localhost 8013
"""

from diesel import Application, Service, until_eol, send

def hi_server(addr):
    while 1:
        inp = until_eol()
        if inp.strip() == b'quit':
            break
        send(b'you said ' + inp)

app = Application()
app.add_service(Service(hi_server, 8013))
app.run()
