from distutils.core import setup, Extension
from Cython.Distutils import build_ext

zlib_wrapper = Extension(
	'spdy._zlib_stream', ['cython/zlib_stream.pyx'],
	libraries=['z']
)

setup(
	name='spdy',
	cmdclass={'build_ext': build_ext},
	ext_modules=[zlib_wrapper],
	packages=['spdy'],
	package_dir={'spdy': 'python-spdy'}
)
