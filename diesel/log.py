
__all__ = (
	'DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'FAILURE', 'CRITICAL',
	'trace', 'fields', 'debug', 'info', 'warn', 'warning', 'error', 'critical',
	'emit',
)

import sys
import time
import logging
import warnings
import functools as F

try:
	import ansi.color.fg as fg
except ImportError:
	fg = None

import twiggy

from . import util as U


levels = twiggy.levels

DEBUG    = levels.DEBUG
INFO     = levels.INFO
NOTICE   = levels.NOTICE
WARNING  = levels.WARNING
ERROR    = levels.ERROR
FAILURE  = levels.ERROR
CRITICAL = levels.CRITICAL

diesel_log = twiggy.log.name('diesel')

name     = diesel_log.name
trace    = diesel_log.trace
fields   = diesel_log.fields
debug    = diesel_log.debug
info     = diesel_log.info
warn     = diesel_log.warning
warning  = diesel_log.warning
error    = diesel_log.error
critical = diesel_log.critical
#failure  = twiggy.log.failure (for twisted:Failure, see txbr)

initialized = False


def emit(*args, **kwargs):
	level = str(kwargs.pop('level', 'info')).lower()
	getattr(twiggy.log, level, debug)(*args, **kwargs)


def xxx_set_log_level(level=INFO):
	if twiggy.emitters:
		for emitter in twiggy.emitters.values():
			emitter.__init__(level, emitter.filter, self._output)
	else:
		quickSetup(level)


def quickSetup(min_level=DEBUG, file=None, format=None):
	if file is None or file == '-':
		file = sys.stderr

	if file is sys.stderr or file is sys.stdout:
		if format is None:
			format = DevelFormat()
		output = twiggy.outputs.StreamOutput(format, stream=file)
	else:
		if format is None:
			format = twiggy.formats.line_format
		output = twiggy.outputs.FileOutput(file, format=format, mode='a')

	assert '*' not in twiggy.emitters, twiggy.emitters
	twiggy.emitters['*'] = twiggy.filters.Emitter(min_level, True, output)

	global initialized
	initialized = True

	catchLogging()
	catchWarnings()


class DevelFormat(twiggy.formats.LineFormat):
	def __init__(self):
		conversion = [
			('time',  str, lambda key, value: None),
#			('time',  F.partial(time.strftime, '%H:%M:%S'), '{1}'.format),
			('level', str, self.format_level, True),
		]

		conversion += [
			('name', str, lambda key, value: '{' + value + '}'),
		] if fg is None else [
			('name', str, lambda key, value: fg.white('{' + value + '}')),
		]

		conversion = twiggy.lib.converter.ConversionTable(conversion)

		conversion.generic_value = lambda value: U.safestr(value) if value is not None else None
		conversion.generic_item  = (
			lambda key, value: '{}={}'.format(key, value) if value else ''
		) if fg is None else (
			lambda key, value: fg.white('{}={}'.format(key, value)) if value else ''
		)
		conversion.aggregate = ' '.join

		super().__init__(separator=' ', traceback_prefix='\n    ', conversion=conversion)

#	def __call__(self, msg):
#		fields = self.format_fields(msg)
#		text   = self.format_text(msg)
#		trace  = self.format_traceback(msg)
#		return '{fields}{self.separator}{text}{trace}\n'.format(**locals())

	if fg is None:
		def format_level(self, key, value):
			return '[{}]'.format(value)

	else:
		def format_level(self, key, value):
			lovalue = value.lower()
			if lovalue in ('error', 'critical'):
				return fg.red('[{}]'.format(value))
			if lovalue in ('warn', 'warning'):
				return fg.yellow('[{}]'.format(value))
			if lovalue in ('debug',):
				return fg.cyan('[{}]'.format(value))
			return '[{}]'.format(value)

		def format_traceback(self, msg):
			return fg.red(super().format_traceback(msg))


def catchWarnings(logger=diesel_log):
	global original_showwarning

	assert warnings.showwarning.__module__ == warnings.__name__, warnings.showwarning
	assert original_showwarning is None, original_showwarning

	original_showwarning = warnings.showwarning

	if logger is diesel_log:
		warnings.showwarning = showwarning
	else:
		warnings.showwarning = F.partial(showwarning, logger=diesel_log)


original_showwarning = None


def showwarning(message, category, filename, lineno, file=None, line=None, logger=diesel_log):
	if file is None:
		logger\
			.fields(category=category, filename=filename, lineno=lineno)\
			.warning('{message}', message=message, line=line)
	else:
		original_showwarning(message, category, filename, lineno, file, line)


def catchLogging(logger=diesel_log):
	logging.root.addHandler(TwiggyHandler(logger))


class TwiggyHandler:
	level = logging.NOTSET

	def __init__(self, logger):
		self.logger = logger.options(style='percent')

	def handle(self, record):
		if   record.levelno >= logging.CRITICAL: level = CRITICAL
		elif record.levelno >= logging.ERROR   : level = ERROR
		elif record.levelno >= logging.WARNING : level = WARNING
		elif record.levelno >= logging.INFO    : level = INFO
		else:                                    level = DEBUG

		if level < self.logger.min_level:
			return False

		logger = self.logger\
			.fields(name=record.name, time=time.gmtime(record.created))

		if record.exc_info:
			logger = logger.trace(record.exc_info)

		logger.emit(level, str(record.msg), record.args, {})

		return True
