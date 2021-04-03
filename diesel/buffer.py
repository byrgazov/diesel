
class BufAny:
	pass


class Buffer:
	"""An input buffer.

	Allows socket data to be read immediately and buffered, but
	fine-grained byte-counting or sentinel-searching to be
	specified by consumers of incoming data."""

	def __init__(self):
		self._atinbuf = []
		self._atterm = None
		self._atmark = 0

	def set_term(self, term):
		"""Set the current sentinel.

		`term` is either an int, for a byte count, or
		a string, for a sequence of characters that needs
		to occur in the byte stream."""

		self._atterm = term

	def feed(self, data):
		"""Feed some data into the buffer.

		The buffer is appended, and the check() is run in case
		this append causes the sentinel to be satisfied."""

		if type(data) is not bytes:
			raise TypeError('Expected <bytes> got {}'.format(type(data)))

		self._atinbuf.append(data)
		self._atmark += len(data)

		return self.check()

	def clear_term(self):
		self._atterm = None

	def check(self):
		"""Look for the next message in the data stream based on
		the current sentinel."""

		if self._atterm is None:
			return

		if self._atterm is BufAny:
			if self.has_data:
				return self.pop()
			return

		if type(self._atterm) is int:
			buf = None
			ind = self._atterm if self._atterm <= self._atmark else None

		elif type(self._atterm) is bytes:
			buf = b''.join(self._atinbuf)
			res = buf.find(self._atterm)
			ind = res + len(self._atterm) if res != -1 else None

		else:
			raise TypeError('`term` must be a <int>, <bytes>, <BufAny> or <None>', type(self._atterm))

		if ind is not None:
			self._atterm = None  # this terminator was used

			if buf is None:
				buf = b''.join(self._atinbuf)

			use     = buf[:ind]
			new_buf = buf[ind:]
			self._atinbuf = [new_buf]
			self._atmark = len(new_buf)

			return use

	def pop(self):
		b = b''.join(self._atinbuf)
		self._atinbuf = []
		self._atmark = 0
		return b

	@property
	def has_data(self):
		return bool(self._atinbuf)
