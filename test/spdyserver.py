import socket
import ssl
import spdy.frames
import spdy
from pprint import pprint

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 9599))
server.listen(5)

ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ctx.load_cert_chain('server.crt', 'server.key')
ctx.set_npn_protocols(['spdy/2'])

def handle_frame(conn, f):
	print("CLIENT SAYS,", f)
		
	if isinstance(f, spdy.frames.Ping):
		ping = spdy.frames.Ping(f.uniq_id)
		conn.put_frame(ping)	
		print(str(ping) + ", SAYS SERVER")

	elif isinstance(f, spdy.frames.SynStream):
		resp = spdy.frames.SynReply(f.stream_id, {'status': '200 OK', 'version': 'HTTP/1.1'}, flags=0)
		conn.put_frame(resp)
		print(str(resp) + ", SAYS SERVER")
		data = spdy.frames.DataFrame(f.stream_id, b"hello, world!", flags=1)
		conn.put_frame(data)
		print(str(data) + ", SAYS SERVER")

try:
	while True:
		try:
			sock, sockaddr = server.accept()
			ss = ctx.wrap_socket(sock, server_side=True)

			conn = spdy.Context(spdy.SERVER) 

			while True:
				d = ss.recv(1024)
				conn.incoming(d)
				while True:
					f = conn.get_frame()
					if not f:
						break
					handle_frame(conn, f)

				outgoing = conn.outgoing()
				if outgoing: 
					ss.sendall(outgoing)

		except Exception as exc:
			print(exc)
			if not "EOF" in str(exc): raise
			continue

finally:
	server.close()
