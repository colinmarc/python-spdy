from distutils.core import setup, Extension
from Cython.Distutils import build_ext

zlib_wrapper = Extension(
	'spdy._zlib_stream', ['cython/zlib_stream.pyx'],
	libraries=['z']
)

setup(
	name='spdy',
	version='0.2',
	description='a parser/muxer/demuxer for spdy frames',
	author='Colin Marc',
	author_email='colinmarc@gmail.com',
	url='http//www.github.com/colinmarc/python-spdy',
	requires=['Cython (>=0.15.1)', 'bitarray (>=0.7.0)'],
	cmdclass={'build_ext': build_ext},
	ext_modules=[zlib_wrapper],
	packages=['spdy'],
	package_dir={'spdy': 'python-spdy'}
)
