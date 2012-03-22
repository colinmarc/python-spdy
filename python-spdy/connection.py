from spdy.frames import *
from spdy._zlib_stream import Inflater, Deflater


SPDY_2 = 'SPDY_2'
VERSIONS = {
	2: SPDY_2
}

SERVER = 'SERVER'
CLIENT = 'CLIENT'

def _ignore_first_bit(n, l):
	return n & int('0' + ''.join(['1' for p in range(l-1)]), 2)

class Connection:
	def __init__(self, side, version=2):
		if side not in [SERVER, CLIENT]:
			raise TypeError("side must be SERVER or CLIENT")

		long_version = VERSIONS.get(version, False)
		if not version:
			raise NotImplementedError()
		self.version = version
		self.long_version = long_version

		self.deflater = Deflater()
		self.inflater = Inflater()
		self.frame_queue = []
		self.input_buffer = b''

	def incoming(self, chunk):
		self.input_buffer += chunk

	def get_frame(self):
		frame, bytes_parsed = self._parse_frame(self.input_buffer)
		if bytes_parsed:
			self.input_buffer = self.input_buffer[bytes_parsed:]
		return frame

	def put_frame(self, frame):
		if not isinstance(frame, Frame):
			raise TypeError("frame must be a valid Frame object")
		self.frame_queue.append(frame)

	def outgoing(self, frame):
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
		if not isinstance(chunk, bytes):
			raise TypeError('chunk must be a bytes string')

		if len(chunk) < 8:
			return (0, None)

		#first bit: control or data frame?
		control_frame = (chunk[0] & 0b10000000 == 128)

		if control_frame:
			#second byte (and rest of first, after the first bit): spdy version
			spdy_version = _ignore_first_bit(int.from_bytes(chunk[0:2], 'big'), 16)

			#third and fourth byte: frame type
			ft = int.from_bytes(chunk[2:4], 'big')
			frame_type = FRAME_TYPES.get(ft, False)
			if not frame_type:
				raise SpdyProtocolError("invalid frame type: {0}".format(ft))

			#fifth byte: flags
			flags = chunk[4]

			#sixth, seventh and eighth bytes: length
			length = int.from_bytes(chunk[5:8], 'big')
			frame_length = length + 8
			if len(chunk) < frame_length:
				return (0, None)

			print(spdy_version, self.version, frame_type, flags, length) 

			if spdy_version != self.version:
				raise SpdyProtocolError("incorrect SPDY version")

			if frame_type == SYN_STREAM:
				#ninth through twelvth bytes, except for the first bit: stream_id
				stream_id = _ignore_first_bit(int.from_bytes(chunk[8:12], 'big'), 32)
				
				#thirteenth through sixteenth bytes, except for the first bit: associated stream_id
				assoc_stream_id = _ignore_first_bit(int.from_bytes(chunk[12:16], 'big'), 32)
				
				#first 2 bits of seventeenth byte: priority
				priority = chunk[16] & 0b1100000000000000

				#ignore the rest of the seventeenth and the whole eighteenth byte (they are reserved)
				#the rest is a header block
				headers = self._parse_header_chunk(chunk[18:length+8])
				frame = SynStream(spdy_version, stream_id, headers)

				print(headers)

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
			frame_length = 8 + length
			if len(chunk) < frame_length:
				return (0, None)

			data = chunk[8:frame_length]
			frame = DataFrame(stream_id, frame_length)

		return (frame, frame_length)
