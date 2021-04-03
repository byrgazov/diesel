
import sys, os
import select
import subprocess
import setuptools

assert sys.version_info >= (3, 5), 'Diesel requires python 3.5'

#if os.system("which palmc > /dev/null 2>&1") == 0:
#	os.system("palmc ./diesel/protocols ./diesel/protocols")

additional_requires = []

if os.environ.get('DIESEL_LIBEV') or os.environ.get('DIESEL_NO_EPOLL') or not hasattr(select, 'epoll'):
	additional_requires.append('pyev')

VERSION = '3.5.0'


def setup():
	setuptools.setup(
		name   ='diesel',
		version=VERSION,
		author ='Jamie Turner/Boomplex LLC/Bump Technologies, Inc/Various Contributors',
		author_email='jamie@bu.mp',
		description ='Diesel is a coroutine-based networking library for Python',
		long_description="""
diesel is a framework for easily writing reliable and scalable network
applications in Python.  It uses the greenlet library layered atop
asynchronous socket I/O in Python to achieve benefits of both
the threaded-style (linear, blocking-ish code flow) and evented-style
(no locking, low overhead per connection) concurrency paradigms. It's
design is heavily inspired by the Erlang/OTP platform.

It contains high-quality buffering, queuing and synchronization primitives,
procedure supervision and supervision trees, connection pools, seamless
thread integration, and more.

An HTTP/1.1+WSGI+WebSockets implementation is included.

Other bundled protocols include MongoDB, Riak, and Redis client libraries.
""",
		url='http://diesel.io',
		packages=[
			'diesel',
			'diesel.protocols',
			'diesel.util',
			'diesel.util.patches',
			'diesel.protocols.http',
		],
		scripts=['examples/dhttpd'],
		entry_points={
			'console_scripts': [
				'dpython = diesel.interactive:python',
				'idpython = diesel.interactive:ipython',
				'dnosetests = diesel.dnosetests:main',
				'dconsole = diesel.console:main',
			],
		},
		install_requires=[
			'greenlet',
			'twiggy',
			'pyopenssl',
#			'flask',
			'werkzeug',
			'http-parser >= 0.7.12',
			'dnspython',
		] + additional_requires,
		cmdclass = {
			'build_protos': build_protos,
		},
	)


class build_protos(setuptools.Command):
	description = 'build_protos'

	user_options = [
		('inplace', 'i', 'ignore build-lib and put compiled extensions into the source directory '\
			'alongside your pure Python modules'),
	]

	inplace    = False
	build_lib  = None
	build_temp = None

	def initialize_options(self):
		pass

	def finalize_options(self):
		self.set_undefined_options('build_ext',
			('inplace',    'inplace'),
			('build_lib',  'build_lib'),
			('build_temp', 'build_temp'))

	def run(self):
#		dist = self.distribution
#		dist.fetch_build_eggs([REQ_PROTOBUF])

		# @todo: ...

#		if self.inplace:
#			build_py = self.get_finalized_command('build_py')
#			pkgdir   = os.path.abspath(build_py.get_package_dir('diesel'))
#			builddir = os.path.join(pkgdir, 'protos')
#		else:
#			builddir = os.path.join(self.build_lib, 'nyokong', 'borders')
#			os.makedirs(builddir, 0o750, True)

		protos = [
			'examples/kv.proto',
			'diesel/convoy/convoy_env.proto',
			'diesel/protocols/riak.proto',
		]

		for filename in protos:
			subprocess.check_output(['protoc',
				'--python_out', '.',
				filename
			])

#		dist.fetch_build_eggs(['pyrobuf==0.6.4'])
#		import pyrobuf.parse_proto3
#		parser = pyrobuf.parse_proto3.Proto3Parser()
#		from pyrobuf.__main__ import gen_message
#		gen_message('borders/nyokong', proto3=True)


if __name__ == '__main__':
	setup()
