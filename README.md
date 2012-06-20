python-spdy
==========

python-spdy is a simple spdy parser/(de)muxer for python >= 2.7 (including 3.x).

usage
-----
```python

import spdy, spdy.frames

#with an existing socket or something
context = spdy.Context(side=spdy.SERVER, version=2)

while True:
	data = sock.recv(1024)
	if not data:
		break

	context.incoming(data)

	while True:
		frame = context.get_frame()
		if not frame: 
			break
		
		if isinstance(frame, spdy.frames.Ping):
			pong = spdy.frames.Ping(frame.ping_id)
			context.put_frame(pong)

	outgoing = context.outgoing()
	if outgoing:
		sock.sendall(outgoing)	
```
installation
------------

requires:

	pip install cython bitarray

then:
	
	python setup.py install


