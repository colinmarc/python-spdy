DEFAULT_VERSION = 2
VERSIONS = [2]

SYN_STREAM = 1
SYN_REPLY = 2
RST_STREAM = 3
SETTINGS = 4
NOOP = 5
PING = 6
GOAWAY = 7
HEADERS = 8
WINDOW_UPDATE = 9

FRAME_TYPES = {
	SYN_STREAM: SynStream,
	SYN_REPLY: SynReply,
	RST_STREAM: RstStream,
#	4: Settings, #TODO
#	5: Noop,
	PING: Ping,
	GOAWAY: Goaway,
	HEADERS: Headers
	WINDOW_UPDATE: WindowUpdate
}

PROTOCOL_ERROR = 1
INVALID_STREAM = 2
REFUSED_STREAM = 3
UNSUPPORTED_VERSION = 4
CANCEL = 5
INTERNAL_ERROR = 6
FLOW_CONTROL_ERROR = 7

ERROR_CODES = {
	1: 'PROTOCOL_ERROR',
	2: 'INVALID_STREAM',
	3: 'REFUSED_STREAM',
	4: 'UNSUPPORTED_VERSION',
	5: 'CANCEL',
	6: 'INTERNAL_ERROR',
	7: 'FLOW_CONTROL_ERROR'
}

FLAG_FIN = 0x01
FLAG_UNID = 0x02

class InvalidFrameError(Exception):
	pass

#definition format
#definition = [
#   (attr or value, num_bits)
#	...
#]
# false for attr means ignore, string means that attribute, int means value
# -1 for num_bits means 'until the end'

#for isinstance(f, Frame) =)
class Frame(object):
	pass

class DataFrame(Frame):
	"""
	+----------------------------------+
	|C|      Stream-ID (31 bits)       |
	+----------------------------------+
	| Flags (8) |    Length (24 bits)  |
	+----------------------------------+
	| Data                             |
	+----------------------------------+
	"""

	def __init__(self, stream_id, data, flags=FLAG_FIN):
		self.is_control = False
		self.stream_id = stream_id
		self.data = data
		self.flags = flags
		self.fin = (flags & FLAG_FIN == FLAG_FIN)

	def __repr__(self):
		return 'DATA ({0}) id={1}'.format(len(self.data), self.stream_id)

class ControlFrame(Frame):
	"""
	+----------------------------------+
	|C| Version(15bits) | Type(16bits) |
	+----------------------------------+
	| Flags (8) |    Length (24 bits)  |
	+----------------------------------+
	| Data                             |
	+----------------------------------+
	"""

	def __init__(self, frame_type, flags=0, version=DEFAULT_VERSION):
		self.is_control = True
		self.frame_type = frame_type
		self.flags = flags
		self.version = version

	def __repr__(self):
		return '? CTRL'

class SynStream(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      1        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|X|     Stream-ID (31bits)         |
	+----------------------------------+
	|X|Associated-To-Stream-ID (31bits)|
	+----------------------------------+
	| Pri|Unused |Slot |               |
	+-------------------               |
	|      Name/value header block     |
	|               ...                |
	+----------------------------------+
	"""
	
	definition = [
		(False, 1), ('stream_id', 31),
		(False, 1), ('assoc_stream_id', 31),
		('priority', 2), (False, 5), ('slot', 8),
		('headers', -1)
	]

	def __init__(self, stream_id, headers, priority=0, assoc_stream_id=0, slot=0, flags=FLAG_FIN, version=DEFAULT_VERSION):
		super(SynStream, self).__init__(SYN_STREAM, flags, version)
		self.stream_id = stream_id
		self.assoc_stream_id = assoc_stream_id
		self.headers = headers
		self.priority = priority
		self.slot = slot
		self.flags = flags
		self.fin = (flags & FLAG_FIN == FLAG_FIN)
		self.unidirectional = (flags & FLAG_UNID == FLAG_UNID)

	def __repr__(self):
		return 'SYN_STREAM id={0}'.format(self.stream_id)

class SynReply(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      2        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|X|     Stream-ID (31bits)         |
	+----------------------------------+
	|     Unused       |               |
	+-------------------               |
	|      Name/value header block     |
	|               ...                |
	+----------------------------------+
	"""
	
	definition = [
		(False, 1), ('stream_id', 31),
		(False, 16),
		('headers', -1)
	]

	def __init__(self, stream_id, headers, flags=0, version=DEFAULT_VERSION):
		super(SynReply, self).__init__(SYN_REPLY, flags, version)
		self.stream_id = stream_id
		self.headers = headers
		self.fin = (flags & FLAG_FIN == FLAG_FIN)

	def __repr__(self):
		return 'SYN_REPLY id={0}'.format(self.stream_id)

class Headers(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      8        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|X|     Stream-ID (31bits)         |
	+----------------------------------+
	|      Unused     |                |
	+------------------                |
	|      Name/value header block     |
	|               ...                |
	+----------------------------------+
	"""
	
	definition = [
		(False, 1), ('stream_id', 31),
		(False, 16),
		('headers', -1)
	]

	def __init__(self, stream_id, headers, flags=0, version=DEFAULT_VERSION):
		super(Headers, self).__init__(HEADERS, 0, version)
		self.stream_id = stream_id
		self.headers = headers

	def __repr__(self):
		return 'HEADERS id={0}'.format(self.stream_id)

class RstStream(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      3        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|X|     Stream-ID (31bits)         |
	+----------------------------------+
	|         Status code              |
	+----------------------------------+
	"""
	
	definition = [
		(False, 1), ('stream_id', 31),
		('error_code', 32)
	]

	def __init__(self, stream_id, error_code, flags=0, version=DEFAULT_VERSION):
		super(RstStream, self).__init__(RST_STREAM, 0, version)
		self.stream_id = stream_id
		self.error_code = error_code

	def __repr__(self):
		return 'RST_STREAM error={0}'.format(ERROR_CODES[self.error_code])

class Ping(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      6        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|                ID                |
	+----------------------------------+
	"""
	
	definition = [
		('uniq_id', 32)
	]

	def __init__(self, uniq_id, flags=0, version=DEFAULT_VERSION):
		super(Ping, self).__init__(PING, 0, version)
		self.uniq_id = uniq_id

	def __repr__(self):
		return 'PING id={0}'.format(self.uniq_id)
	
class Goaway(ControlFrame):
	"""
	+----------------------------------+
	|1|      version   |      7        |
	+----------------------------------+
	| Flags (8) |     Length (24 bits) |
	+----------------------------------+
	|X|  Last-good-stream-ID (31 bits) |
	+----------------------------------+
	"""
	
	definition = [
		('last_stream_id', 32)
	]
	
	def __init__(self, last_stream_id, flags=0, version=DEFAULT_VERSION):
		super(Goaway, self).__init__(GOAWAY, 0, version)
		self.last_stream_id = last_stream_id

	def __repr__(self):
		return 'GET THE FUCK OUT'

class WindowUpdate(ControlFrame):
	"""
	+----------------------------------+
	|1|   version    |         9       |
	+----------------------------------+
	| 0 (flags) |     8 (length)       |
	+----------------------------------+
	|X|     Stream-ID (31-bits)        |
	+----------------------------------+
	|X|  Delta-Window-Size (31-bits)   |
	+----------------------------------+
	"""
	
	definition = [
		(False, 1), ('stream_id', 31),
		(False, 1), ('delta_window_size', 31)

	def __init__(self, stream_id, delta_window_size, flags=0, version=DEFAULT_VERSION):
		if version < 3:
			raise InvalidFrameError("WINDOW_UPDATE only exists in spdy/3 and greater")

		super(WindowUpdate, self).__init__(WINDOW_UPDATE, 0, version))
		self.stream_id = stream_id
		self.delta_window_size = delta_window_size

