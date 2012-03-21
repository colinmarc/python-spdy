import socket
import ssl

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('', 9599))
server.listen(5)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ctx.load_cert_chain('server.crt', 'server.key')
ctx.set_npn_protocols(['spdy/2'])
b = bytearray()
try:
	while True:
		try:
			sock, sockaddr = server.accept()
			ss = ctx.wrap_socket(sock, server_side=True)
		except Exception as exc:
			print(exc)
			continue

		while True:
			d = ss.recv(1024)
			b.extend(d)
			print(d)
finally:
	server.close()
	print(b)
