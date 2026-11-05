#include <Python.h>
static PyObject *add(PyObject *self, PyObject *args) { long a, b; if (!PyArg_ParseTuple(args, "ll", &a, &b)) return NULL; return PyLong_FromLong(a + b); }
static PyMethodDef methods[] = {{"add", add, METH_VARARGS, NULL}, {NULL, NULL, 0, NULL}};
static PyModuleDef_Slot slots[] = {{Py_mod_gil, Py_MOD_GIL_NOT_USED}, {0, NULL}};
static struct PyModuleDef mod = {PyModuleDef_HEAD_INIT, "_core", NULL, 0, methods, slots};
PyMODINIT_FUNC PyInit__core(void) { return PyModuleDef_Init(&mod); }
