SYN_STREAM = 1
SYN_REPLY = 2
RST_STREAM = 3
SETTINGS = 4
NOOP = 5
PING = 6
GOAWAY = 7
HEADERS = 8

FRAME_TYPES = {
	1: 'SYN_STREAM',
	2: 'SYN_REPLY',
	3: 'RST_STREAM',
	4: 'SETTINGS',
	5: 'NOOP',
	6: 'PING',
	7: 'GOAWAY',
	8: 'HEADERS'
}


class SpdyProtocolError(Exception):
	pass

#for isinstance(f, Frame) =)
class Frame(object):
	pass

class DataFrame(Frame):
	def __init__(self, stream_id, data=None, fin=True):
		self.is_control = False
		self.stream_id = stream_id
		self.data = data
		self.fin = False

class ControlFrame(Frame):
	def __init__(self, version, frame_type):
		self.is_control = True
		self.version = version
		self.frame_type = frame_type

	def __repr__(self):
		return FRAME_TYPES[self.frame_type]

class SynStream(ControlFrame):
	def __init__(self, version, stream_id, headers, fin=True, unidirectional=False):
		super(SynStream, self).__init__(version, SYN_STREAM)
		self.stream_id = stream_id
		self.headers = headers
		self.fin = fin
		self.unidirectional = unidirectional

class SynReply(ControlFrame):
	def __init__(self, version, stream_id, headers, fin=True):
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

	def __repr__(self):
		return 'GET THE FUCK OUT'

