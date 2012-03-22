from spdy.connection import *

server = Connection(SERVER)
client = Connection(CLIENT)

frame = SynStream(2, client.next_stream_id, {'dood': 'balls', 'stuff': 'otherstuff'})
client.put_frame(frame)
chunk = client.outgoing()

server.incoming(chunk)
frame2 = server.get_frame()
print(frame2.headers)
