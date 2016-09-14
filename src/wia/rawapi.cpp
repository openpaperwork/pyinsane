#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include <windows.h>
#include <atlbase.h>
#include <wia.h>
#include <Sti.h>

#include <Python.h>

#define WIA_WARNING(msg) do { \
        PyErr_WarnEx(NULL, (msg), 1); \
        fprintf(stderr, (msg)); \
        fprintf(stderr, "\n"); \
    } while(0)

#define WIA_PYCAPSULE_DEV_NAME "WIA device"
#define WIA_PYCAPSULE_SRC_NAME "WIA source"

struct wia_device {
    IWiaDevMgr2 *dev_manager;
    IWiaItem2 *device;
};

struct wia_source {
#define WIA_SRC_AUTO 0
#define WIA_SRC_FLATBED 1
#define WIA_SRC_FEEDER 2
    int type;
    struct wia_device *dev;
    IWiaItem2 *source;
};

static PyObject *init(PyObject *, PyObject* args)
{
    HRESULT hr;

	if (!PyArg_ParseTuple(args, "")) {
		return NULL;
	}

    hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WARNING: CoInitialize() failed !");
        Py_RETURN_NONE;
    }

	Py_RETURN_NONE;
}


static HRESULT get_device_basic_infos(IWiaPropertyStorage *properties,
    PyObject **out_tuple)
{
    PyObject *devid, *devname;
    PROPSPEC input[3] = {0};
    PROPVARIANT output[3] = {0};
    HRESULT hr;

    *out_tuple = NULL;

    input[0].ulKind = PRSPEC_PROPID;
    input[0].propid = WIA_DIP_DEV_ID;
    input[1].ulKind = PRSPEC_PROPID;
    input[1].propid = WIA_DIP_DEV_NAME;
    input[2].ulKind = PRSPEC_PROPID;
    input[2].propid = WIA_DIP_DEV_TYPE;

    hr = properties->ReadMultiple(3 /* nb_properties */, input, output);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WiaPropertyStorage->ReadMultiple() failed");
        return hr;
    }

    assert(output[0].vt == VT_BSTR);
    assert(output[1].vt == VT_BSTR);
    assert(output[2].vt == VT_I4);

    if (GET_STIDEVICE_TYPE(output[2].lVal) != StiDeviceTypeScanner) {
        *out_tuple = NULL;
        return S_OK;
    }

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
        WIA_WARNING("Pyinsane: WARNING: CoCreateInstance failed");
        Py_RETURN_NONE;
    }

    hr = wia_dev_manager->EnumDeviceInfo(WIA_DEVINFO_ENUM_LOCAL, &wia_dev_info_enum);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WARNING: WiaDevMgr->EnumDviceInfo() failed");
        Py_RETURN_NONE;
    }

    // Get the numeber of WIA devices

    hr = wia_dev_info_enum->GetCount(&nb_devices);
    if (FAILED(hr)) {
        WIA_WARNING("PyInsane: WARNING: GetCount() failed !");
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
        if (dev_infos == NULL) {
            // not a scanner
            continue;
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

    wia_dev = (struct wia_device *)PyCapsule_GetPointer(device, WIA_PYCAPSULE_DEV_NAME);
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
        WIA_WARNING("Pyinsane: WARNING: CoCreateInstance failed");
        Py_RETURN_NONE;
    }

    dev = (struct wia_device *)calloc(1, sizeof(struct wia_device));
    dev->dev_manager = wia_dev_manager;

    bstr_devid = SysAllocString(A2W(devid)); // TODO(Jflesch): Does any of this allocate anything ? oO
    hr = wia_dev_manager->CreateDevice(0, bstr_devid, &dev->device);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WARNING: WiaDevMgr->CreateDevice() failed");
        free(dev);
        Py_RETURN_NONE;
    }

    return PyCapsule_New(dev, WIA_PYCAPSULE_DEV_NAME, free_device);
}

static void free_source(PyObject *source)
{
    struct wia_source *wia_src;

    wia_src = (struct wia_source *)PyCapsule_GetPointer(source, WIA_PYCAPSULE_DEV_NAME);
    // TODO
    free(wia_src);
}

static PyObject *get_sources(PyObject *, PyObject *args)
{
    struct wia_device *dev;
    IEnumWiaItem2 *enum_item;
    IWiaItem2 *child;
    PyObject *source_name;
    PyObject *capsule;
    PyObject *tuple;
    PyObject *all_sources;
    struct wia_source *source;
    PROPSPEC input[2] = {0};
    PROPVARIANT output[2] = {0};
    HRESULT hr;

    input[0].ulKind = PRSPEC_PROPID;
    input[0].propid = WIA_IPA_FULL_ITEM_NAME;
    input[1].ulKind = PRSPEC_PROPID;
    input[1].propid = WIA_IPA_ITEM_CATEGORY;

    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        WIA_WARNING("Pyinsane: get_sources(): Invalid args");
        return NULL;
    }
    if (!PyCapsule_CheckExact(capsule)) {
        WIA_WARNING("Pyinsane: WARNING: get_sources(): invalid argument type (not a pycapsule)");
        Py_RETURN_NONE;
    }

    if ((dev = (struct wia_device *)PyCapsule_GetPointer(capsule, WIA_PYCAPSULE_DEV_NAME)) == NULL) {
        WIA_WARNING("Pyinsane: WARNING: get_sources(): invalid argument type");
        Py_RETURN_NONE;
    }

    all_sources = PyList_New(0);

    hr = dev->device->EnumChildItems(NULL, &enum_item);
    while(hr == S_OK) {
        hr = enum_item->Next(1, &child, NULL);
        if (hr != S_OK) {
            continue;
        }

        CComQIPtr<IWiaPropertyStorage> child_properties(child);

        source = (struct wia_source *)calloc(2, sizeof(struct wia_source));
        source->dev = dev;
        source->source = child;

        hr = child_properties->ReadMultiple(2 /* nb_properties */, input, output);
        if (FAILED(hr)) {
            WIA_WARNING("Pyinsane: WiaPropertyStorage->ReadMultiple() failed");
            child->Release();
            continue;
        }

        assert(output[0].vt == VT_BSTR);
        assert(output[1].vt == VT_CLSID);

        if (*output[1].puuid == WIA_CATEGORY_FINISHED_FILE
                    || *output[1].puuid == WIA_CATEGORY_FOLDER
                    || *output[1].puuid == WIA_CATEGORY_ROOT) {
                free(source);
                continue;
        } else if (*output[1].puuid == WIA_CATEGORY_AUTO) {
                source->type = WIA_SRC_AUTO;
        } else if (*output[1].puuid == WIA_CATEGORY_FEEDER
                    || *output[1].puuid == WIA_CATEGORY_FEEDER_BACK
                    || *output[1].puuid == WIA_CATEGORY_FEEDER_FRONT) {
                source->type = WIA_SRC_FEEDER;
        } else {
            source->type = WIA_SRC_FLATBED;
        }

        source_name = PyUnicode_FromWideChar(output[0].bstrVal, -1);
        capsule = PyCapsule_New(source, WIA_PYCAPSULE_SRC_NAME, free_source);
        tuple = PyTuple_Pack(2, source_name, capsule);
        PyList_Append(all_sources, tuple);
    }

    return all_sources;
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
	{"get_sources", get_sources, METH_VARARGS, NULL},
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
