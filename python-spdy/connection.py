from frames import *
from spdy._zlib_stream import Inflater, Deflater

HEADER_ZLIB_DICT = \
	b"optionsgetheadpostputdeletetraceacceptaccept-charsetaccept-encodingaccept-" \
	b"languageauthorizationexpectfromhostif-modified-sinceif-matchif-none-matchi" \
	b"f-rangeif-unmodifiedsincemax-forwardsproxy-authorizationrangerefererteuser" \
	b"-agent10010120020120220320420520630030130230330430530630740040140240340440" \
	b"5406407408409410411412413414415416417500501502503504505accept-rangesageeta" \
	b"glocationproxy-authenticatepublicretry-afterservervarywarningwww-authentic" \
	b"ateallowcontent-basecontent-encodingcache-controlconnectiondatetrailertran" \
	b"sfer-encodingupgradeviawarningcontent-languagecontent-lengthcontent-locati" \
	b"oncontent-md5content-rangecontent-typeetagexpireslast-modifiedset-cookieMo" \
	b"ndayTuesdayWednesdayThursdayFridaySaturdaySundayJanFebMarAprMayJunJulAugSe" \
	b"pOctNovDecchunkedtext/htmlimage/pngimage/jpgimage/gifapplication/xmlapplic" \
	b"ation/xhtmltext/plainpublicmax-agecharset=iso-8859-1utf-8gzipdeflateHTTP/1" \
	b".1statusversionurl"

SPDY_2 = 'SPDY_2'
VERSIONS = {
	2: SPDY_2
}

SERVER = 'SERVER'
CLIENT = 'CLIENT'

def _ignore_first_bit(n):
	return n << 1 >> 1 #discard the first bit

class Connection:
	def __init__(self, side, version=2):
		if side not in [SERVER, CLIENT]:
			raise TypeError("side must be SERVER or CLIENT")

		version = VERSIONS.get(version, False)
		if not version:
			raise NotImplementedError()
		self.version = version

		self.deflater = Deflater(dictionary=ZLIB_HEADER_DICT)
		self.inflater = Inflater(dictionary=ZLIB_HEADER_DICT)
		self.frame_queue = []
		self.input_buffer = b''

	def incoming(chunk):
		self.input_buffer += chunk

	def get_frame():
		bytes_parsed, frame = self._parse_frame(self.input_buffer)
		if bytes_parsed:
			self.input_buffer = self.input_buffer[bytes_parsed:]
		return frame

	def put_frame(frame):
		if not isinstance(frame, Frame):
			raise TypeError("frame must be a valid Frame object")
		self.frame_queue.append(frame)

	def outgoing():
		out = bytearray()
		while len(self.frame_queue) > 0:
			frame = self.frame_queue.pop(0)
			out.extend(self._encode_frame(frame))
		return out

	def _parse_header_chunk(chunk, zlib_stream):
		num_values = int.from_bytes(chunk[0:2], 'big')	

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
			frame_length = length + 8
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
			frame_length = 8 + length
			if len(chunk) < frame_length:
				return (0, None)

			data = chunk[8:frame_length]
			frame = DataFrame(stream_id, frame_length)

		return (frame, frame_length)
