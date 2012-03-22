SYN_STREAM = 'SYN_STREAM'
SYN_REPLY = 'SYN_REPLY'
RST_STREAM = 'RST_STREAM'
SETTINGS = 'SETTINGS'
NOOP = 'NOOP'
PING = 'PING'
GOAWAY = 'GOAWAY'
HEADERS = 'HEADERS'

FRAME_TYPES = {
	1: SYN_STREAM,
	2: SYN_REPLY,
	3: RST_STREAM,
	4: SETTINGS,
	5: NOOP,
	6: PING,
	7: GOAWAY,
	8: HEADERS
}


class SpdyProtocolError(Exception):
	pass

#for isinstance(f, Frame) =)
class Frame(object):
	pass

class DataFrame(Frame):
	def __init__(self, stream, data=None, raw=None):
		self.is_control = False
		self.stream_id = stream_id
		self._raw = None
		self._data = data

	def __repr__(self):
		if self._data:
			return 'DATA ({1})'.format(len(self._data))
		else:
			return 'DATA (uncompressed)'

	@property
	def data(self):
		if not self._data:
			self._decompress_raw()
		return self._data

	@data.setter
	def data(self, data):
		self._data = data

	@data.deleter
	def data(self):
		del self._data
	
	def _decompress_raw(self):
		raise NotImplementedError()

class ControlFrame(Frame):
	def __init__(self, version, frame_type):
		self.is_control = True
		self.version = version
		self.frame_type = frame_type

	def __repr__(self):
		return self.frame_type

	#abstract
	def _parse(self):
		raise NotImplementedError()

	#abstract
	def _encode(self):
		raise NotImplementedError()

#class HeaderBlock:
#	def __init__(self, headers):
#		self._headers = headers
#
#	@property
#	def headers(self):
#		if not self._headers:
#			self._parse()
#		return self._headers
#
#	@headers.setter
#	def headers(self, headers):
#		self._headers = headers
#	
#	@headers.deleter
#	def headers(self):
#		del self._headers

class SynStream(ControlFrame):
	def __init__(self, version, stream_id, headers=None):
#		ControlFrame.__init__(self, version, SYN_STREAM)
#		HeaderBlock.__init__(self, headers)
		super(SynStream, self).__init__(version, SYN_STREAM)
		self.stream_id = stream_id

class SynReply(ControlFrame):
	def __init__(self, version, stream_id, headers=None):
#		ControlFrame.__init__(self, version, SYN_REPLY)
#		HeaderBlock.__init__(self, headers)
		super(SynReply, self).__init__(version, SYN_HEADERS)
		self.stream_id = stream_id
	
class Headers(ControlFrame):
	def __init__(self, version, stream_id, headers=None):
#		ControlFrame.__init__(self, version, HEADERS)
#		HeaderBlock.__init__(self, headers)
		super(Headers, self).__init__(version, HEADERS)
		self.stream_id = stream_id

class RstStream(ControlFrame):
	def __init__(self, version, stream_id, error_code):
		super(RstStream, self).__init__(version, RST_STREAM)
		self.stream_id = stream_id
		self.error_code = error_code


