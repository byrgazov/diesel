"""The oh-so-canonical "Hello, World!" http server."""

from diesel import Application, Service
from diesel.protocols import http

def hello_http(req):
    return http.Response("Hello, World!")

app = Application()
app.add_service(Service(http.HttpServer(hello_http), 8088))

#import profile
#profile.run('app.run()')

app.run()
