#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include <windows.h>
#include <atlbase.h>
#include <wia.h>

#include <Python.h>

PyObject *init(PyObject *self, PyObject* args)
{
    HRESULT hr;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        fprintf(stderr, "Pyinsane: WARNING: CoInitialize() failed !\n");
        Py_RETURN_NONE;
    }

	//Py_BEGIN_ALLOW_THREADS;
	//Py_END_ALLOW_THREADS;

	Py_RETURN_NONE;
}

PyObject *get_devices(PyObject *self, PyObject* args)
{
    HRESULT hr;
    CComPtr<IWiaDevMgr> pWiaDevMgr;
    CComPtr<IEnumWIA_DEV_INFO> pIEnumWIA_DEV_INFO;
    unsigned long nb_devices;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    // Create a connection to the local WIA device manager
    hr = pWiaDevMgr.CoCreateInstance(CLSID_WiaDevMgr);
    if (FAILED(hr)) {
        fprintf(stderr, "Pyinsane: WARNING: CoCreateInstance failed\n");
        Py_RETURN_NONE;
    }

    hr = pWiaDevMgr->EnumDeviceInfo(0, &pIEnumWIA_DEV_INFO);
    if (FAILED(hr))
    {
        fprintf(stderr, "Pyinsane: WARNING: WiaDevMgr->EnumDviceInfo() failed\n");
        Py_RETURN_NONE;
    }

    // Get the number of WIA devices

    hr = pIEnumWIA_DEV_INFO->GetCount(&nb_devices);
    if (FAILED(hr))
    {
        fprintf(stderr, "PyInsane: WARNING: GetCount() failed !\n");
        Py_RETURN_NONE;
    }

    fprintf(stderr, "NB devices: %d\n", nb_devices);

	//Py_BEGIN_ALLOW_THREADS;
	//Py_END_ALLOW_THREADS;

	Py_RETURN_NONE;
}


static PyMethodDef rawapi_methods[] = {
	{"init", init, METH_VARARGS, NULL},
	{"get_devices", get_devices, METH_VARARGS, NULL},
	{NULL, NULL, 0, NULL},
};

#if PY_VERSION_HEX < 0x03000000

PyMODINIT_FUNC
init_rawapi(void)
{
    Py_InitModule("_rawapi", rawapi_methods);
}

#else

static struct PyModuleDef rawapi_module = {
	PyModuleDef_HEAD_INIT,
	"_rawapi",
	NULL /* doc */,
	-1,
	rawapi_methods,
};

PyMODINIT_FUNC PyInit__rawapi(void)
{
	return PyModule_Create(&rawapi_module);
}
#endif
