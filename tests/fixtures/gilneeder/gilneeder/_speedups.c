#include <Python.h>
static PyObject *add(PyObject *self, PyObject *args) { long a, b; if (!PyArg_ParseTuple(args, "ll", &a, &b)) return NULL; return PyLong_FromLong(a + b); }
static PyMethodDef methods[] = {{"add", add, METH_VARARGS, NULL}, {NULL, NULL, 0, NULL}};
static struct PyModuleDef mod = {PyModuleDef_HEAD_INIT, "_speedups", NULL, -1, methods};
PyMODINIT_FUNC PyInit__speedups(void) { return PyModule_Create(&mod); }
