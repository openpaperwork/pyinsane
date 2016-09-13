#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include <windows.h>
#include <atlbase.h>
#include <wia.h>

#include <Python.h>

#define WIA_PYCAPSULE_NAME "WIA device"

struct wia_device {
    IWiaDevMgr2 *dev_manager;
    IWiaItem2 *device;
};

static PyObject *init(PyObject *, PyObject* args)
{
    HRESULT hr;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WARNING: CoInitialize() failed !", 1);
        Py_RETURN_NONE;
    }

	Py_RETURN_NONE;
}


static HRESULT get_device_basic_infos(IWiaPropertyStorage *properties,
    PyObject **out_tuple)
{
    PyObject *devid, *devname;
    PROPSPEC input[2] = {0};
    PROPVARIANT output[2] = {0};

    *out_tuple = NULL;

    input[0].ulKind = PRSPEC_PROPID;
    input[0].propid = WIA_DIP_DEV_ID;
    input[1].ulKind = PRSPEC_PROPID;
    input[1].propid = WIA_DIP_DEV_NAME;

    HRESULT hr = properties->ReadMultiple(2 /* nb_properties */, input, output);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WiaPropertyStorage->ReadMultiple() failed", 1);
        return hr;
    }

    assert(output[0].vt == VT_BSTR);
    assert(output[1].vt == VT_BSTR);

    devid = PyUnicode_FromWideChar(output[0].bstrVal, -1);
    devname = PyUnicode_FromWideChar(output[1].bstrVal, -1);

    *out_tuple = PyTuple_Pack(2, devid, devname);

    FreePropVariantArray(2, output);

    return S_OK;
}


static PyObject *get_devices(PyObject *, PyObject* args)
{
    HRESULT hr;
    CComPtr<IWiaDevMgr2> wia_dev_manager;
    CComPtr<IEnumWIA_DEV_INFO> wia_dev_info_enum;
    unsigned long nb_devices;
    PyObject *dev_infos;
    PyObject *all_devs;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    // Create a connection to the local WIA device manager
    hr = wia_dev_manager.CoCreateInstance(CLSID_WiaDevMgr2);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WARNING: CoCreateInstance failed", 1);
        Py_RETURN_NONE;
    }

    hr = wia_dev_manager->EnumDeviceInfo(WIA_DEVINFO_ENUM_LOCAL, &wia_dev_info_enum);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WARNING: WiaDevMgr->EnumDviceInfo() failed", 1);
        Py_RETURN_NONE;
    }

    // Get the numeber of WIA devices

    hr = wia_dev_info_enum->GetCount(&nb_devices);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "PyInsane: WARNING: GetCount() failed !", 1);
        Py_RETURN_NONE;
    }

    all_devs = PyList_New(0);

    while (hr == S_OK) {
        IWiaPropertyStorage *properties = NULL;
        hr = wia_dev_info_enum->Next(1, &properties, NULL);
        if (hr != S_OK || properties == NULL)
            break;

        hr = get_device_basic_infos(properties, &dev_infos);
        if (FAILED(hr)) {
            Py_RETURN_NONE;
        }

        properties->Release();

        PyList_Append(all_devs, dev_infos);
    }

    // wia_dev_info_enum->Release(); // TODO(Jflesch) ?
    return all_devs;
}

static void free_device(PyObject *device)
{
    struct wia_device *wia_dev;

    wia_dev = (struct wia_device *)PyCapsule_GetPointer(device, WIA_PYCAPSULE_NAME);
    // TODO
    free(wia_dev);
}

static PyObject *open_device(PyObject *, PyObject *args)
{
    char *devid;
    CComPtr<IWiaDevMgr2> wia_dev_manager;
    struct wia_device *dev;
    BSTR bstr_devid;
    HRESULT hr;
    USES_CONVERSION;

    if (!PyArg_ParseTuple(args, "s", &devid)) {
        return NULL;
    }

    hr = wia_dev_manager.CoCreateInstance(CLSID_WiaDevMgr2);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WARNING: CoCreateInstance failed", 1);
        Py_RETURN_NONE;
    }

    dev = (struct wia_device *)calloc(1, sizeof(struct wia_device));
    dev->dev_manager = wia_dev_manager;

    bstr_devid = SysAllocString(A2W(devid)); // TODO(Jflesch): Does any of this allocate anything ? oO
    hr = wia_dev_manager->CreateDevice(0, bstr_devid, &dev->device);
    if (FAILED(hr)) {
        PyErr_WarnEx(NULL, "Pyinsane: WARNING: WiaDevMgr->CreateDevice() failed", 1);
        free(dev);
        Py_RETURN_NONE;
    }

    return PyCapsule_New(dev, WIA_PYCAPSULE_NAME, free_device);
}


static PyObject *exit(PyObject *, PyObject* args)
{
    if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    CoUninitialize();

	Py_RETURN_NONE;
}


static PyMethodDef rawapi_methods[] = {
	{"init", init, METH_VARARGS, NULL},
	{"get_devices", get_devices, METH_VARARGS, NULL},
	{"open", open_device, METH_VARARGS, NULL},
	{"exit", exit, METH_VARARGS, NULL},
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
