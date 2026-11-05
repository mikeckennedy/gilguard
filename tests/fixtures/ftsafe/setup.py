from setuptools import Extension, setup

setup(name='ftsafe', version='0.3.0', packages=['ftsafe'], ext_modules=[Extension('ftsafe._core', ['ftsafe/_core.c'])])
