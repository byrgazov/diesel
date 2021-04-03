# -*- coding: utf-8 -*-

__all__ = ('safestr', 'strictstr')


def safestr(data, encoding='utf8'):
	if isinstance(data, str):
		return data

	try:
		try:
			if isinstance(data, bytes):
				data = str(data, encoding, 'replace')
			else:
				data = str(data)
		except UnicodeError:
			data = repr(data)
	except Exception as exc:
		data = 'FATAL ERROR IN safestr: [{}] {}'.format(type(exc).__name__, exc)

	return data


def strictstr(text, encoding='latin1'):
	if isinstance(text, bytes):
		return str(text.decode(encoding))
	elif isinstance(text, str):
		return str(text)
	raise TypeError('strictstr must receive a <bytes> or <str> object', type(text))
