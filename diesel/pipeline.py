"""An outgoing pipeline that can handle strings or files."""

import io
import bisect


def make_BIO(d):
	t = io.BytesIO()
	t.write(d)
	t.seek(0)
	return t


def get_file_length(f):
	m = f.tell()
	f.seek(0, 2)
	r = f.tell()
	f.seek(m)
	return r


class PipelineCloseRequest(Exception):
	pass


class PipelineClosed(Exception):
	pass


class PipelineItem:
	def __init__(self, d):
		if type(d) is bytes:
			self.f = make_BIO(d)
			self.length = len(d)
			self.is_io = True
			self.f.seek(0, 2)
		elif hasattr(d, 'seek') and not isinstance(d, io.TextIOBase) and not getattr(d, 'encoding', None):
			self.f = d
			self.length = get_file_length(d)
			self.is_io = False
		else:
			raise TypeError('Argument to add() must be either a <bytes> or a <file-like object> (raw), got {}'.format(type(d)))

		self.read = self.f.read

	def merge(self, s):
		self.f.write(s)
		self.length += len(s)

	def reset(self):
		if self.is_io:
			self.is_io = False
			self.f.seek(0, 0)

	@property
	def done(self):
		return self.f.tell() == self.length

	def __eq__(self, other):
		if other is PipelineStandIn:
			return False
		return id(self) == id(other)

	def __lt__(self, other):
		if other is PipelineStandIn:
			return True
		return id(self) < id(other)

	def __lte__(self, other):
		if other is PipelineStandIn:
			return True
		return id(self) <= id(other)

	def __gt__(self, other):
		if other is PipelineStandIn:
			return False
		return id(self) > id(other)

	def __gte__(self, other):
		if other is PipelineStandIn:
			return False
		return id(self) >= id(other)


class PipelineStandIn:
	pass


class Pipeline:
	"""A pipeline that supports appending bytes or
	files and can read() transparently across object
	boundaries in the outgoing buffer."""

	def __init__(self):
		self.line = []
		self.current = None
		self.want_close = False

	def add(self, data, priority=5):
		"""Add object `data` to the pipeline."""

		if self.want_close:
			raise PipelineClosed

		priority *= -1

		dummy = (priority, PipelineStandIn)
		ind   = bisect.bisect_right(self.line, dummy)

		if 0 < ind and type(data) is bytes and self.line[ind - 1][-1].is_io:
			a_pri, adjacent = self.line[ind - 1]
			if adjacent.is_io and a_pri == priority:
				adjacent.merge(data)
			else:
				self.line.insert(ind, (priority, PipelineItem(data)))
		else:
			self.line.insert(ind, (priority, PipelineItem(data)))

	def close_request(self):
		"""Add a close request to the outgoing pipeline.

		No more data will be allowed in the pipeline, and, when
		it is emptied, PipelineCloseRequest will be raised."""
		self.want_close = True

	def read(self, amt):
		"""Read up to `amt` bytes off the pipeline.

		May raise PipelineCloseRequest if the pipeline is
		empty and the connected stream should be closed.
		"""

		if not self.current and not self.line:
			if self.want_close:
				raise PipelineCloseRequest()
			return b''

		if not self.current:
			_, self.current = self.line.pop(0)
			self.current.reset()

		out = b''

		while len(out) < amt:
			try:
				data = self.current.read(amt - len(out))
			except ValueError:
				data = b''

			if data == b'':
				if not self.line:
					self.current = None
					break
				_, self.current = self.line.pop(0)
				self.current.reset()
			else:
				out += data

		# eagerly evict and EOF that's been read _just_ short of
		# the EOF '' read() call.. so that we know we're empty,
		# and we don't bother with useless iterations
		if self.current and self.current.done:
			self.current = None

		return out

	def backup(self, d):
		'''Pop object d back onto the front the pipeline.

		Used in cases where not all data is sent() on the socket,
		for example--the remainder will be placed back in the pipeline.
		'''
		cur = self.current
		self.current = PipelineItem(d)
		self.current.reset()
		if cur:
			self.line.insert(0, (-1000000, cur))

	@property
	def empty(self):
		'''Is the pipeline empty?

		A close request is "data" that needs to be consumed,
		too.
		'''
		return self.want_close == False and not self.line and not self.current
