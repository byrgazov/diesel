# -*- coding: utf-8 -*-

"""HTTP/1.1 implementation of client and server.

@xxx: [bw] (!!!) это сплошная порнография, требуется полный рефакторинг
"""

import os
import io
import time
import datetime
import urllib.parse

#from flask import Request, Response
import werkzeug

try:
	from OpenSSL import SSL
except ImportError:
	SSL = None

try:
	from http_parser.parser import HttpParser
except ImportError:
	from http_parser.pyparser import HttpParser

from diesel import receive, ConnectionClosed, send, log, Client, call, first


utcnow   = datetime.datetime.utcnow
urlparse = urllib.parse.urlparse
unquote  = urllib.parse.unquote

hlog = log.name('http-error')

Request  = werkzeug.Request
Response = werkzeug.Response

SERVER_TAG = 'diesel-http-server'
HOSTNAME   = os.uname()[1]  # @xxx: (!!!) hostname


def parse_request_line(line):
	"""Given a request line, split it into (method, url, protocol)."""

	items = line.split(' ')
	items[0] = items[0].upper()

	if len(items) == 2:
		return tuple(items) + ('0.9',)

	items[1] = unquote(items[1])
	items[2] = items[2].split('/')[-1].strip()

	return tuple(items)


class FileLikeErrorLogger:
	def __init__(self, logger):
		self.logger = logger

	def write(self, s):
		self.logger.error(s)

	def writelines(self, lns):
		self.logger.error('\n'.join(list(lns)))

	def flush(self):
		pass


class HttpServer:
	"""An HTTP/1.1 implementation of a server."""

	def __init__(self, request_handler):
		"""Create an HTTP server that calls `request_handler` on requests.

	`request_handler` is a callable that takes a `Request` object and
	generates a `Response`.

	To support WebSockets, if the `Response` generated has a `status_code` of
	101 (Switching Protocols) and the `Response` has a `new_protocol` method,
	it will be called to handle the remainder of the client connection."""

		self.request_handler = request_handler

	def on_service_init(self, service):
		"""Called when this connection handler is connected to a Service."""
		self.port = service.port

	def __call__(self, addr):
		"""Since an instance of HttpServer is passed to the Service
	class (with appropriate request_handler established during
	initialization), this __call__ method is what's actually
	invoked by diesel."""

		data = None

		while True:
			try:
				parser = HttpParser()
				body   = []

				while True:
					if data:
						used = parser.execute(data, len(data))
						if parser.is_headers_complete():
							body.append(parser.recv_body())
						if parser.is_message_complete():
							data = data[used:]
							break
					data = receive()

				env = parser.get_wsgi_environ()

				if 'HTTP_CONTENT_LENGTH' in env:
					env['CONTENT_LENGTH'] = env.pop('HTTP_CONTENT_LENGTH')

				if 'HTTP_CONTENT_TYPE' in env:
					env['CONTENT_TYPE'] = env.pop('HTTP_CONTENT_TYPE')

				env.update({
					'wsgi.version': (1,0),
					'wsgi.url_scheme': 'http',  # @todo: (!) Incomplete
					'wsgi.input'  : io.BytesIO(b''.join(body)),
					'wsgi.errors' : FileLikeErrorLogger(hlog),
					'wsgi.multithread' : False,
					'wsgi.multiprocess': False,
					'wsgi.run_once'    : False,
					'REMOTE_ADDR': addr[0],
					'SERVER_NAME': HOSTNAME,
					'SERVER_PORT': str(self.port),
				})

				req = Request(env)

				if req.headers.get('Connection', '').lower() == 'upgrade':
					req.data = data

				resp = self.request_handler(req)

				if 'Server' not in resp.headers:
					resp.headers.add('Server', SERVER_TAG)

				if 'Date' not in resp.headers:
					resp.headers.add('Date', utcnow().strftime('%a, %d %b %Y %H:%M:%S UTC'))

				assert resp, 'HTTP request handler _must_ return a response'

				self.send_response(resp, version=parser.get_version())

				if not parser.should_keep_alive() \
				   or resp.headers.get('Connection', '').lower() == 'close' \
				   or resp.headers.get('Content-Length') == None:
					return

				# Switching Protocols

				if resp.status_code == 101 and hasattr(resp, 'new_protocol'):
					resp.new_protocol(req)
					break
			except ConnectionClosed:
				break

	def send_response(self, resp, version=(1,1)):
		if 'X-Sendfile' in resp.headers:
			sendfile = resp.headers.pop('X-Sendfile')
			size = os.stat(sendfile).st_size
			resp.headers.set('Content-Length', size)
		else:
			sendfile = None

		send('HTTP/{}.{} {} {}\r\n'.format(*version, resp.status_code, resp.status).encode('latin1'))
		send(str(resp.headers).encode('latin1'))

		if sendfile:
			send(open(sendfile, 'rb'))  # diesel can stream fds
		else:
			for i in resp.iter_encoded():
				send(i)


class HttpRequestTimeout(Exception):
    pass


class TimeoutHandler:
    def __init__(self, timeout):
        self._timeout = timeout
        self._start = time.time()

    def remaining(self, raise_on_timeout=True):
        remaining = self._timeout - (time.time() - self._start)
        if remaining < 0 and raise_on_timeout:
            self.timeout()
        return remaining

    def timeout(self):
        raise HttpRequestTimeout()


def cgi_name(n):
	if n.lower() in ('content-type', 'content-length'):
		# Certain headers are defined in CGI as not having an HTTP
		# prefix.
		return n.upper().replace('-', '_')

	return 'HTTP_' + n.upper().replace('-', '_')


class HttpClient(Client):
	"""An HttpClient instance that issues 1.1 requests,
	including keep-alive behavior.

	Does not support sending chunks, yet... body must
	be a string."""

	url_scheme = "http"

	@call
	def request(self, method, path, headers=None, body=None, timeout=None):
		"""Issues a `method` request to `path` on the
		connected server.  Sends along `headers`, and
		body.

		Very low level--you must set "host" yourself,
		for example.  It will set Content-Length,
		however.
		"""

		if type(path) is bytes:
			path = path.decode('utf-8')

		scheme = 'https' if self.port == 443 else 'http'
		netloc = self.addr
		path   = path.split('#', 1)[0]

		if '?' in path:
			path, query = path.split('?', 1)
		else:
			query = ''

		headers   = headers or {}
		fake_wsgi = {cgi_name(n): str(v).strip() for n, v in headers.items()}

		if body and 'CONTENT_LENGTH' not in fake_wsgi:
			# If the caller hasn't set their own Content-Length but submitted
			# a body, we auto-set the Content-Length header here.
			fake_wsgi['CONTENT_LENGTH'] = str(len(body))

		fake_wsgi.update({
			'REQUEST_METHOD' : method,
			'SCRIPT_NAME'    : '',
			'PATH_INFO'      : path,
			'QUERY_STRING'   : query,
			'wsgi.version'   : (1, 0),
			'wsgi.url_scheme': scheme,
			'wsgi.input'     : io.BytesIO(body or b''),
			'wsgi.errors'    : FileLikeErrorLogger(hlog),
			'wsgi.multithread' : False,
			'wsgi.multiprocess': False,
			'wsgi.run_once'    : False,
		})

		req = Request(fake_wsgi)

		timeout_handler = TimeoutHandler(timeout or 60)

		url = str(req.path)

		if req.query_string:
			url += '?' + str(req.query_string)

		send('{} {} HTTP/1.1\r\n{}'.format(req.method, url, str(req.headers)).encode('latin1'))

		if body:
			send(body)

		parser = HttpParser()

		body = []
		data = None

		while True:
			if data:
				used = parser.execute(data, len(data))

				if parser.is_headers_complete():
					body.append(parser.recv_body())

				if parser.is_message_complete():
					data = data[used:]
					break

			ev, val = first(receive_any=True, sleep=timeout_handler.remaining())

			if ev == 'sleep':
				timeout_handler.timeout()

			data = val

		resp = Response(
			response=b''.join(body),
			status  =parser.get_status_code(),
			headers =parser.get_headers(),
		)

		return resp


class HttpsClient(HttpClient):
	url_scheme = 'https'

	if SSL is not None:
		def __init__(self, *args, **kw):
			kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
			super().__init__(*args, **kw)
	else:
		def __init__(self, *args, **kw):
			raise ImportError('No module named \'OpenSSL\'')
