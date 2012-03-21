import zlib

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
		self._raw = None

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

def ignore_first_bit(n, l):
	return n & int('0' + ''.join(['1' for p in range(l-1)]), 2)



def parse_frame(chunk):
	if not isinstance(chunk, bytes):
		raise TypeError('chunk must be a bytes string')

	if len(chunk) < 8:
		return (0, None)

	#first bit: control or data frame?
	control_frame = (chunk[0] & 0b10000000 == 128)

	if control_frame:
		#second byte (and rest of first, after the first bit): spdy version
		spdy_version = ignore_first_bit(int.from_bytes(chunk[0:2], 'big'), 16)

		#third and fourth byte: frame type
		ft = int.from_bytes(chunk[2:4], 'big')
		frame_type = FRAME_TYPES.get(ft, False)
		if not frame_type:
			raise SpdyProtocolError("invalid frame type: {0}".format(ft))

		#fifth byte: flags
		flags = chunk[4]

		#sixth, seventh and eighth bytes: length
		length = int.from_bytes(chunk[5:8], 'big')
		frame_length
		if len(chunk) < frame_length:
			return (0, None)

		print(spdy_version, frame_type, flags, length) 

		if frame_type == SYN_STREAM:
			#ninth through twelvth bytes, except for the first bit: stream_id
			stream_id = ignore_first_bit(int.from_bytes(chunk[8:12], 'big'), 32)
			
			#thirteenth through sixteenth bytes, except for the first bit: associated stream_id
			assoc_stream_id = ignore_first_bit(int.from_bytes(chunk[12:16], 'big'), 32)
			
			#first 2 bits of seventeenth byte: priority
			priority = chunk[16] & 0b1100000000000000

			#ignore the rest of the seventeenth and the whole eighteenth byte. the rest is a header block
			header_chunk = parse_header_chunk(chunk[18:length+8])
		elif frame_type == SYN_REPLY:
			raise NotImplementedError()
		elif frame_type == RST_STREAM:
			raise NotImplementedError()
		elif frame_type == SETTINGS:
			raise NotImplementedError()
		elif frame_type == NOOP:
			raise NotImplementedError()
		elif frame_type == PING:
			raise NotImplementedError()
		elif frame_type == GOAWAY:
			raise NotImplementedError()
		elif frame_type == HEADERS:
			raise NotImplementedError()
		else:
			raise NotImplementedError()

	else: #data frame
		#second, third and fourth bytes (and rest of first): stream_id
		#TODO: account for stream_ids > 32767
		stream_id = int.from_bytes(chunk[1:4], 'big')
		
		#fifth byte: flags
		flags = chunk[4]

		#sixth, seventh and eight bytes: length
		length = int.from_bytes(chunk[5:8], 'big')
		if len(chunk) < 8 + length:
			return (0, None)

		

	return (frame, 8 + length)

if __name__ == '__main__':
	b = b'\x80\x02\x00\x01\x01\x00\x01\x0e\x00\x00\x00\x01\x00\x00\x00\x00\x00\x008\xea\xdf\xa2Q\xb2b\xe0b`\x83\xa4\x17\x06{\xb8\x0bu0,\xd6\xae@\x17\xcd\xcd\xb1.\xb45\xd0\xb3\xd4\xd1\xd2\xd7\x02\xb3,\x18\xf8Ps,\x83\x9cg\xb0?\xd4=:`\x07\x81\xd5\x99\xeb@\xd4\x1b3\xf0\xa3\xe5i\x06A\x90\x8bu\xa0N\xd6)NI\xce\x80\xab\x81%\x03\x06\xbe\xd4<\xdd\xd0`\x9d\xd4<\xa8\xa5,\xa0<\xce\xc0\x07J\x089 \xa6\x95\xa5\xa9\xa5%\x03[.\xb0l\xc9Oa`vw\ra`+\x06&\xc7\xdcT\x06\xd6\x8c\x92\x92\x82b\x06f\x90\xbf\x19\xf5\x19\xb8\x10\x99\x95\x01\x18\xf5U\x9999\x89\xfa\xa6z\x06\n\x1a\x11\x00\x19\x1aZ+\xf8d\xe6\x95V(d\x9aY\x98i*8\x02}\x9e\x1a\x9e\x9a\xe4\x9dY\xa2ojl\xaagh\xa8\xa0\xe1\xed\x11\xe2\xeb\xa3\xa3\x90\x93\x99\x9d\xaa\xe0\x9e\x9a\x9c\x9d\xaf\xa9\xe0\x9c\x01,sR\xf5\r\xcd\xf5\x80\x01cf\xacgn\xa9\x10\x9c\x98\x96X\x94\t\xd5\xc4\xc0\x0e\ry\x06\x0eX\x84\x00\x00\x00\x00\xff\xff\x80\x02\x00\x06\x00\x00\x00\x04\x00\x00\x00\x01'

	parse_frame(b)

