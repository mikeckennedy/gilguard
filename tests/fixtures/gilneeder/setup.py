from setuptools import Extension, setup

setup(
    name='gilneeder',
    version='1.2.0',
    packages=['gilneeder'],
    ext_modules=[Extension('gilneeder._speedups', ['gilneeder/_speedups.c'])],
)
