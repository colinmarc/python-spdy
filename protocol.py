import zlib

SYN_STREAM = 'SYN_STREAM'
SYN_REPLY = 'SYN_REPLY'
RST_STREAM = 'RST_STREAM'
SETTINGS = 'SETTINGS'
NOOP = 'NOOP'
PING = 'PING'
GOAWAY = 'GO:AWAY'
HEADERS = 'HEADERS'
WINDOW_UPDATE = 'WINDOW_UPDATE'

class Frame(object):
	pass

class DataFrame(Frame):
	def __init__(self, stream, data=None):
		self.is_control = False
		self.stream_id = stream_id
		self._raw = None
		self._data = data

	@property
	def data(self):
		if not self._data:
			self._parse()
		return self._data

	@data.setter
	def data(self, data):
		self._data = data

	@data.deleter
	def data(self):
		del self._data
	
	def _parse(self):
		raise NotImplemented()

class ControlFrame(Frame):
	def __init__(self, frame_type):
		self.is_control = True
		self.frame_type = frame_type
		self._raw = None

	#abstract
	def _parse(self):
		raise NotImplemented

	#abstract
	def _encode(self):
		raise NotImplemented

class HeaderBlock:
	def __init__(self, headers):
		self._headers = headers

	@property
	def headers(self):
		if not self._headers:
			self._parse()
		return self.headers

	@headers.setter
	def headers(self, headers):
		self._headers = headers
	
	@headers.deleter
	def headers(self)
		del self._headers

class SynStream(ControlFrame, HeaderBlock):
	def __init__(self, stream_id, headers):
		ControlFrame.__init__(self, SYN_STREAM)
		HeaderBlock.__init__(self, headers)
		self.stream_id = stream_id

class SynReply(ControlFrame, HeaderBlock):
	def __init__(self, stream_id, headers):
		ControlFrame.__init__(self, SYN_REPLY)
		HeaderBlock.__init__(self, headers)
		self.stream_id = stream_id
	
class Headers(ControlFrame, HeaderBlock):
	def __init__(self, stream_id, headers):
		ControlFrame.__init__(self, HEADERS)
		HeaderBlock.__init__(self, headers)
		self.stream_id = stream_id

class RstStream(ControlFrame):
	def __init__(self, stream_id, error_code):
		super(RstStream, self).__init__(RST_STREAM)
		self.stream_id = stream_id
		self.error_code = error_code

