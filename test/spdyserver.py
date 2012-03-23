import socket
import ssl
import spdy.frames
from spdy.connection import *
from pprint import pprint

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 9599))
server.listen(5)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ctx.load_cert_chain('server.crt', 'server.key')
ctx.set_npn_protocols(['spdy/2'])

def handle_frame(conn, f):
	print("server says,", f)
		
	if isinstance(f, spdy.frames.Ping):
		ping = spdy.frames.Ping(f.uniq_id)
		conn.put_frame(ping)	
		print(ping, "says client")
	elif isinstance(f, spdy.frames.SynStream):
		pprint(f.headers)	
		resp = spdy.frames.SynReply(f.stream_id, {'status': '200 OK', 'version': 'HTTP/1.1'}, flags=0)
		conn.put_frame(resp)
		print(resp, "says client")
		data = spdy.frames.DataFrame(f.stream_id, b"hello world!!!", flags=1)
		conn.put_frame(data)
		print(data, "says client")

try:
	while True:
		try:
			sock, sockaddr = server.accept()
			ss = ctx.wrap_socket(sock, server_side=True)

			conn = Connection(SERVER) 

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
