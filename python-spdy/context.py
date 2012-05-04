from spdy.frames import *
from spdy._zlib_stream import Inflater, Deflater
from bitarray import bitarray

SERVER = 'SERVER'
CLIENT = 'CLIENT'

class SpdyProtocolError(Exception):
	pass

def _bitmask(length, split, mask=0):
	invert = 1 if mask == 0 else 0
	b = str(mask)*split + str(invert)*(length-split)
	return int(b, 2)

_first_bit = _bitmask(8, 1, 1)
_last_15_bits = _bitmask(16, 1, 0)

class Context(object):
	def __init__(self, side, version=2):
		if side not in (SERVER, CLIENT):
			raise TypeError("side must be SERVER or CLIENT")

		if not version in VERSIONS:
			raise NotImplementedError()
		self.version = version

		self.deflater = Deflater(version)
		self.inflater = Inflater(version)
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

	def _parse_header_chunk(self, compressed_data, version):
		chunk = self.inflater.decompress(compressed_data)
		length_size = 2 if version == 2 else 4	
		headers = {}

		#first two bytes: number of pairs
		num_values = int.from_bytes(chunk[0:length_size], 'big')	

		#after that...
		cursor = length_size
		for _ in range(num_values):
			#two/four bytes: length of name
			name_length = int.from_bytes(chunk[cursor:cursor+length_size], 'big')
			cursor += length_size

			#next name_length bytes: name
			name = chunk[cursor:cursor+name_length].decode('UTF-8')
			cursor += name_length
			
			#two/four bytes: length of value
			value_length = int.from_bytes(chunk[cursor:cursor+length_size], 'big')
			cursor += length_size

			#next value_length bytes: value
			value = chunk[cursor:cursor+value_length].decode('UTF-8')
			cursor += value_length
			
			if name_length == 0 or value_length == 0:
				raise SpdyProtocolError("zero-length name or value in n/v block")
			if name in headers:
				raise SpdyProtocolError("duplicate name in n/v block")
			headers[name] = value

		return headers

	def _parse_frame(self, chunk):
		if len(chunk) < 8:
			return (None, 0)

		#first bit: control or data frame?
		control_frame = (chunk[0] & _first_bit == _first_bit)

		if control_frame:
			#second byte (and rest of first, after the first bit): spdy version
			spdy_version = int.from_bytes(chunk[0:2], 'big') & _last_15_bits
			if spdy_version != self.version:
				raise SpdyProtocolError("incorrect SPDY version")

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
				return (None, 0)

			#the rest is data
			data = chunk[8:frame_length]

			bits = bitarray()
			bits.frombytes(data)
			frame_cls = FRAME_TYPES[frame_type]

			args = {
				'version': spdy_version,
				'flags': flags
			}

			for key, num_bits in frame_cls.definition(spdy_version):
				if not key:
					bits = bits[num_bits:]
					continue

				if num_bits == -1:
					value = bits
				else:
					value = bits[:num_bits]
					bits = bits[num_bits:]
					
				if key == 'headers': #headers are compressed
					args[key] = self._parse_header_chunk(value.tobytes(), self.version)
				else:
					#we have to pad values on the left, because bitarray will assume
					#that you want it padded from the right
					gap = len(value) % 8
					if gap:
						zeroes = bitarray(8 - gap)
						zeroes.setall(False)
						value = zeroes + value
					args[key] = int.from_bytes(value.tobytes(), 'big')
				
				if num_bits == -1:
					break

			frame = frame_cls(**args)

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
			frame = DataFrame(stream_id, data)

		return (frame, frame_length)

	def _encode_header_chunk(self, headers):
		chunk = bytearray()

		#first two bytes: number of pairs
		chunk.extend(len(headers).to_bytes(2, 'big'))

		#after that...
		for name, value in headers.items():
			name = bytes(name, 'UTF-8')
			value = bytes(value, 'UTF-8')

			#two bytes: length of name
			chunk.extend(len(name).to_bytes(2, 'big'))

			#next name_length bytes: name
			chunk.extend(name)

			#two bytes: length of value
			chunk.extend(len(value).to_bytes(2, 'big'))

			#next value_length bytes: value
			chunk.extend(value)
			
		return self.deflater.compress(bytes(chunk))
		
	
	def _encode_frame(self, frame):
		out = bytearray()

		if frame.is_control:
			#first two bytes: version
			out.extend(frame.version.to_bytes(2, 'big'))

			#set the first bit to control
			out[0] = out[0] | _first_bit

			#third and fourth: frame type
			out.extend(frame.frame_type.to_bytes(2, 'big'))

			#fifth: flags
			out.append(frame.flags)

			bits = bitarray()
			for key, num_bits in frame.definition(self.version):

				if not key:
					zeroes = bitarray(num_bits)
					zeroes.setall(False)
					bits += zeroes
					continue

				value = getattr(frame, key)
				if key == 'headers':
					chunk = bitarray()
					chunk.frombytes(self._encode_header_chunk(value))
				else:
					chunk = bitarray(bin(value)[2:])
					zeroes = bitarray(num_bits - len(chunk))
					zeroes.setall(False)
					chunk = zeroes + chunk #pad with zeroes

				bits += chunk
				if num_bits == -1:
					break

			data = bits.tobytes() 

			#sixth, seventh and eighth bytes: length
			out.extend(len(data).to_bytes(3, 'big'))

			# the rest is data
			out.extend(data)
		
		else: #data frame
			
			#first four bytes: stream_id
			out.extend(frame.stream_id.to_bytes(4, 'big'))
			
			#fifth: flags
			out.append(frame.flags)

			#sixth, seventh and eighth bytes: length
			data_length = len(frame.data)
			out.extend(data_length.to_bytes(3, 'big'))
		
			#rest is data
			out.extend(frame.data)

		return out

