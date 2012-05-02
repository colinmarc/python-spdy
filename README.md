python-spdy
==========

python-spdy is a simple spdy parser/(de)muxer for python >= 2.7 (including 3.x).

usage
-----

	import spdy, spdy.frames
	
	#with an existing socket or something
	context = spdy.Context(side=spdy.SERVER, version=2)

	while True:
		data = sock.recv(1024)
		if not data:
			continue

		context.incoming(data)

		while True:
			frame = context.get_frame()
			print(frame)
			
			if isinstance(frame, spdy.frames.Ping):
				pong = spdy.frames.Ping(frame.ping_id)
				context.put_frame(pong)
	
		sock.sendall(context.outgoing())	

installation
------------

requires:

	pip install cython bitarray

then:
	
	python setup.py install


