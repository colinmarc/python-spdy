from spdy.frames import *
from spdy._zlib_stream import Inflater, Deflater


SPDY_2 = 2
VERSIONS = {
	2: 'SPDY_2'
}

SERVER = 'SERVER'
CLIENT = 'CLIENT'

FLAG_FIN = 0x01
FLAG_UNID = 0x02

def _ignore_first_bit(b):
	arr = bytearray()
	arr.append(b[0] & 0b01111111)
	arr.extend(b[1:])
	return bytes(arr)

class Connection:
	def __init__(self, side, version=2):
		if side not in [SERVER, CLIENT]:
			raise TypeError("side must be SERVER or CLIENT")

		if not version in VERSIONS:
			raise NotImplementedError()
		self.version = version

		self.deflater = Deflater()
		self.inflater = Inflater()
		self.frame_queue = []
		self.input_buffer = bytearray()

		if side == SERVER:
			self._stream_id = 2
			self._ping_id = 2
		else:
			self._stream_id = 1
			self._ping_id = 1

	@property
	def next_stream_id(self):
		sid = self._stream_id
		self._stream_id += 2
		return sid

	@property
	def next_ping_id(self):
		pid = self._ping_id
		self._ping_id += 2
		return pid

	def incoming(self, chunk):
		self.input_buffer.extend(chunk)

	def get_frame(self):
		frame, bytes_parsed = self._parse_frame(bytes(self.input_buffer))
		if bytes_parsed:
			self.input_buffer = self.input_buffer[bytes_parsed:]
		return frame

	def put_frame(self, frame):
		if not isinstance(frame, Frame):
			raise TypeError("frame must be a valid Frame object")
		self.frame_queue.append(frame)

	def outgoing(self):
		out = bytearray()
		while len(self.frame_queue) > 0:
			frame = self.frame_queue.pop(0)
			out.extend(self._encode_frame(frame))
		return out

	def _parse_header_chunk(self, compressed_data):
		chunk = self.inflater.decompress(compressed_data)
		headers = {}

		#first two bytes: number of pairs
		num_values = int.from_bytes(chunk[0:2], 'big')	

		#after that...
		cursor = 2
		for _ in range(num_values):
			#two bytes: length of name
			name_length = int.from_bytes(chunk[cursor:cursor+2], 'big')

			#next name_length bytes: name
			name = chunk[cursor+2:cursor+2+name_length].decode('UTF-8')

			#move the cursor up...
			cursor += name_length + 2
			
			#two bytes: length of value
			value_length = int.from_bytes(chunk[cursor:cursor+2], 'big')

			#next value_length bytes: value
			value = chunk[cursor+2:cursor+2+value_length].decode('UTF-8')
			
			#move the cursor up again
			cursor += value_length + 2

			if name_length == 0 or value_length == 0:
				raise SpdyProtocolError("zero-length name or value in n/v block")
			if name in headers:
				raise SpdyProtocolError("duplicate name in n/v block")
			headers[name] = value

		return headers

	def _parse_frame(self, chunk):
		if len(chunk) < 8:
			return (0, None)

		#first bit: control or data frame?
		control_frame = (chunk[0] & 0b10000000 == 128)

		if control_frame:
			#second byte (and rest of first, after the first bit): spdy version
			spdy_version = int.from_bytes(_ignore_first_bit(chunk[0:2]), 'big')

			#third and fourth byte: frame type
			frame_type = int.from_bytes(chunk[2:4], 'big')
			if not frame_type in FRAME_TYPES:
				raise SpdyProtocolError("invalid frame type: {0}".format(frame_type))

			#fifth byte: flags
			flags = chunk[4]

			#sixth, seventh and eighth bytes: length
			length = int.from_bytes(chunk[5:8], 'big')
			frame_length = length + 8
			if len(chunk) < frame_length:
				return (0, None)

			#the rest is data
			data = chunk[8:frame_length]

			if spdy_version != self.version:
				raise SpdyProtocolError("incorrect SPDY version")

			if frame_type == SYN_STREAM:
				fin = (flags & FLAG_FIN == FLAG_FIN)
				unidirectional = (flags & FLAG_UNID == FLAG_UNID)

				#first through fourth bytes, except for the first bit: stream_id
				stream_id = int.from_bytes(_ignore_first_bit(data[0:4]), 'big')
				
				#fifth through eighth bytes, except for the first bit: associated stream_id
				assoc_stream_id = int.from_bytes(_ignore_first_bit(data[4:8]), 'big')
				
				#first 2 bits of ninth byte: priority
				priority = data[8] & 0b1100000000000000

				#ignore the rest of the ninth and the whole tenth byte (they are reserved)
				#the rest is a header block
				headers = self._parse_header_chunk(data[10:])
				frame = SynStream(spdy_version, stream_id, headers, fin, unidirectional)

			elif frame_type == SYN_REPLY:
				raise NotImplementedError()
			elif frame_type == RST_STREAM:
				raise NotImplementedError()
			elif frame_type == SETTINGS:
				raise NotImplementedError()
			elif frame_type == NOOP:
				raise NotImplementedError()
			elif frame_type == PING:
				#all four bytes: uniq_id
				uniq_id = int.from_bytes(data, 'big') 
				frame = Ping(spdy_version, uniq_id)
	
			elif frame_type == GOAWAY:
				#all four bytes, except the first bit: last_stream_id
				last_stream_id = int.from_bytes(_ignore_first_bit(data), 'big')
				frame = Goaway(spdy_version, last_stream_id)

			elif frame_type == HEADERS:
				raise NotImplementedError()
			else:
				raise NotImplementedError()

		else: #data frame
			#first four bytes, except the first bit: stream_id
			stream_id = int.from_bytes(_ignore_first_bit(chunk[0:4]), 'big')
			
			#fifth byte: flags
			flags = chunk[4]

			#sixth, seventh and eight bytes: length
			length = int.from_bytes(chunk[5:8], 'big')
			frame_length = 8 + length
			if len(chunk) < frame_length:
				return (0, None)

			data = chunk[8:frame_length]
			frame = DataFrame(stream_id, frame_length)

		return (frame, frame_length)

	def _encode_header_chunk(self, headers):
		chunk = bytearray()

		#first two bytes: number of pairs
		chunk += len(headers).to_bytes(2, 'big')

		#after that...
		for name, value in headers.items():
			name = bytes(name, 'UTF-8')
			value = bytes(value, 'UTF-8')

			#two bytes: length of name
			chunk += len(name).to_bytes(2, 'big')

			#next name_length bytes: name
			chunk += name

			#two bytes: length of value
			chunk += len(value).to_bytes(2, 'big')

			#next value_length bytes: value
			chunk += value
			
		return self.deflater.compress(bytes(chunk))
		
	
	def _encode_frame(self, frame):
		out = bytearray()

		if frame.is_control:
			#first two bytes: version
			out += frame.version.to_bytes(2, 'big')

			#make sure first bit is control
			out[0] = out[0] | 0b10000000

			#third and fourth: frame type
			out += frame.frame_type.to_bytes(2, 'big')

			#fifth: flags
			out += bytes(1) #set later

			data = bytearray()

			if frame.frame_type == SYN_STREAM:
				#set the flags
				flags = 0
				if frame.fin: flags |= FLAG_FIN
				if frame.unidirectional: flags |= FLAG_UNID
				out[4] = flags

				#first through fourth bytes, except for the first bit: stream_id
				data.extend(frame.stream_id.to_bytes(4, 'big'))
				
				#fifth through eighth bytes, except for the first bit: associated stream_id
				data.extend(bytes(4)) #TODO
				
				#first 2 bits of ninth byte: priority
				#ignore the rest of the ninth and the whole tenth byte (they are reserved)
				data.extend(bytes(2)) #TODO

				#the rest is a header block
				data.extend(self._encode_header_chunk(frame.headers))

			elif frame.frame_type == SYN_REPLY:
				raise NotImplementedError()
			elif frame.frame_type == RST_STREAM:
				raise NotImplementedError()
			elif frame.frame_type == SETTINGS:
				raise NotImplementedError()
			elif frame.frame_type == NOOP:
				raise NotImplementedError()
			elif frame.frame_type == PING:
				#all four bytes: uniq_id
				data = frame.uniq_id.to_bytes(4, 'big') 

			elif frame.frame_type == GOAWAY:
				#all four bytes, except the first bit: last_stream_id
				data = frame.last_stream_id.to_bytes(4, 'big')

			elif frame.frame_type == HEADERS:
				raise NotImplementedError()
			else:
				raise NotImplementedError()

			#sixth, seventh, eigth: length
			out.extend(len(data).to_bytes(3, 'big'))

			# the rest is data
			out.extend(data)
		
		else: #data frame
			#first four bytes: stream_id
			out.extend(frame.stream_id.to_bytes(4, 'big'))
			
			#fifth: flags
			flags = 0
			if frame.fin:
				flags = flags | FLAG_FIN
			out.append(flags)

			#sixth, seventh and eighth bytes: length
			data_length = len(frame.data)
			out.extend(data_length.to_bytes(3, 'big'))
		
			#rest is data
			out.extend(data)

		return out

