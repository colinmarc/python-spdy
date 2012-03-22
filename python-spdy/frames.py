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
	def __init__(self, stream_id, data=None):
		self.is_control = False
		self.stream_id = stream_id
		self.data = data

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

class SynStream(ControlFrame):
	def __init__(self, version, stream_id, headers):
		super(SynStream, self).__init__(version, SYN_STREAM)
		self.stream_id = stream_id
		self.headers = headers

class SynReply(ControlFrame):
	def __init__(self, version, stream_id, headers):
		super(SynReply, self).__init__(version, SYN_HEADERS)
		self.stream_id = stream_id
	
class Headers(ControlFrame):
	def __init__(self, version, stream_id, headers):
		super(Headers, self).__init__(version, HEADERS)
		self.stream_id = stream_id

class RstStream(ControlFrame):
	def __init__(self, version, stream_id, error_code):
		super(RstStream, self).__init__(version, RST_STREAM)
		self.stream_id = stream_id
		self.error_code = error_code

class Ping(ControlFrame):
	def __init__(self, version, uniq_id):
		super(Ping, self).__init__(version, PING)
		self.uniq_id = uniq_id

	def __repr__(self):
		return 'PING {0}'.format(self.uniq_id)
	
class Goaway(ControlFrame):
	def __init__(self, version, last_stream_id):
		super(Goaway, self).__init__(version, GOAWAY)
		self.last_stream_id = last_stream_id

