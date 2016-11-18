#include <assert.h>
#include <iostream>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <atlbase.h>
#include <comdef.h>
#include <windows.h>
#include <wia.h>
#include <Sti.h>

#include <Python.h>

#include "properties.h"
#include "transfer.h"
#include "util.h"

#define WIA_PYCAPSULE_DEV_NAME "WIA device"
#define WIA_PYCAPSULE_SRC_NAME "WIA source"
#define WIA_PYCAPSULE_SCAN_NAME "WIA scan"

struct wia_device {
    IWiaDevMgr2 *dev_manager;
    IWiaItem2 *device;
};

enum wia_src_type {
    WIA_SRC_AUTO = 0,
    WIA_SRC_FLATBED,
    WIA_SRC_FEEDER,
};

struct wia_source {
    wia_src_type type;
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

    hr = wia_dev_manager->EnumDeviceInfo(WIA_DEVINFO_ENUM_ALL, &wia_dev_info_enum);
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
            break;
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
        Py_DECREF(tuple);
    }

    return all_sources;
}


static IWiaItem2 *capsule2item(PyObject *capsule)
{
    struct wia_device *wia_dev;
    struct wia_source *wia_src;

    if (!PyCapsule_CheckExact(capsule)) {
        WIA_WARNING("Pyinsane: WARNING: invalid argument type (not a pycapsule)");
        return NULL;
    }

    if (strcmp(PyCapsule_GetName(capsule), WIA_PYCAPSULE_DEV_NAME) == 0) {
        wia_dev = (struct wia_device *)PyCapsule_GetPointer(capsule, WIA_PYCAPSULE_DEV_NAME);
        if (wia_dev != NULL)
            return wia_dev->device;
    }

    if (strcmp(PyCapsule_GetName(capsule), WIA_PYCAPSULE_SRC_NAME) == 0) {
        wia_src = (struct wia_source *)PyCapsule_GetPointer(capsule, WIA_PYCAPSULE_SRC_NAME);
        if (wia_src != NULL)
            return wia_src->source;
    }

    WIA_WARNING("Pyinsane: WARNING: Invalid argument type (not a known pycapsule type)");
    return NULL;
}


static PyObject *get_properties(PyObject *, PyObject *args)
{
    PyObject *capsule;
    IWiaItem2 *item;
    PROPSPEC *input;
    PROPVARIANT *output;
    int i;
    int nb_properties;
    HRESULT hr;
    PyObject *all_props;
    PyObject *propname;
    PyObject *propvalue;
    PyObject *prop;
    PyObject *ro;
    PyObject *rw;
    PyObject *access_right;
    PyObject *possible_values;


    if (!PyArg_ParseTuple(args, "O", &capsule)) {
        WIA_WARNING("Pyinsane: WARNING: get_sources(): Invalid args");
        return NULL;
    }

    item = capsule2item(capsule);
    if (item == NULL)
        Py_RETURN_NONE;

    for (nb_properties = 0 ; g_wia_all_properties[nb_properties].name != NULL ; nb_properties++)
    { }

    input = (PROPSPEC *)calloc(nb_properties, sizeof(PROPSPEC));
    output = (PROPVARIANT *)calloc(nb_properties, sizeof(PROPVARIANT));

    for (i = 0 ; i < nb_properties ; i++) {
        input[i].ulKind = PRSPEC_PROPID;
        input[i].propid = g_wia_all_properties[i].id;
    }

    CComQIPtr<IWiaPropertyStorage> properties(item);
    hr = properties->ReadMultiple(nb_properties, input, output);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WARNING: WiaPropertyStorage->ReadMultiple() failed");
        free(input);
        free(output);
        Py_RETURN_NONE;
    }
    free(input);

    ro = PyUnicode_FromString("ro");
    rw = PyUnicode_FromString("rw");

    all_props = PyList_New(0);
    for (i = 0 ; i < nb_properties ; i++) {
        if (output[i].vt == 0)
            continue;
        if (output[i].vt != g_wia_all_properties[i].vartype) {
            WIA_WARNING("Pyinsane: WARNING: A property has a type different from the one expected");
            fprintf(stderr, "Pyinsane: WARNING: Got type %d instead of %d for property \"%s\"\n",
                output[i].vt, g_wia_all_properties[i].vartype, g_wia_all_properties[i].name
            );
            continue;
        }
        switch(output[i].vt) {
            case VT_I4:
                propvalue = int_to_pyobject(&g_wia_all_properties[i], output[i].lVal);
                break;
            case VT_UI4:
                propvalue = int_to_pyobject(&g_wia_all_properties[i], output[i].ulVal);
                break;
            case VT_VECTOR | VT_UI2:
                // TODO
                continue;
            case VT_UI1 | VT_VECTOR:
                // TODO
                continue;
            case VT_BSTR:
                propvalue = PyUnicode_FromWideChar(output[i].bstrVal, -1);
                break;
            case VT_CLSID:
                propvalue = clsid_to_pyobject(&g_wia_all_properties[i], *output[i].puuid);
                break;
            default:
                WIA_WARNING("Pyinsane: WARNING: Unknown var type");
                assert(0);
                continue;
        }
        if (propvalue == NULL)
            continue;
        propname = PyUnicode_FromString(g_wia_all_properties[i].name);

        access_right = (g_wia_all_properties[i].rw ? rw : ro);
        Py_INCREF(access_right); // PyTuple_Pack steals the ref

        possible_values = g_wia_all_properties[i].get_possible_values(&g_wia_all_properties[i]);

        prop = PyTuple_Pack(4, propname, propvalue, access_right, possible_values);
        PyList_Append(all_props, prop);
        Py_DECREF(prop);
    }

    free(output);
    return all_props;
}

static int _set_property(IWiaItem2 *item, const struct wia_property *property_spec, PyObject *pyvalue)
{
    HRESULT hr;
    PROPSPEC propspec;
    PROPVARIANT propvalue;

    propspec.ulKind = PRSPEC_PROPID;
    propspec.propid = property_spec->id;

    propvalue.vt = property_spec->vartype;

    switch(property_spec->vartype) {
        case VT_I4:
            propvalue.lVal = pyobject_to_int(property_spec, pyvalue, -1);
            if (propvalue.lVal == -1)
                return 0;
            break;
        case VT_UI4:
            propvalue.ulVal = pyobject_to_int(property_spec, pyvalue, 0xFFFFFF);
            if (propvalue.ulVal == 0xFFFFFF)
                return 0;
            break;
        case VT_VECTOR | VT_UI2:
        case VT_UI1 | VT_VECTOR:
            WIA_WARNING("Pyinsane: WARNING: Vector not supported yet");
            // TODO
            return 0;
        case VT_BSTR:
            WIA_WARNING("Pyinsane: WARNING: String not supported yet");
            // TODO
            return 0;
        case VT_CLSID:
            if (!pyobject_to_clsid(property_spec, pyvalue, &propvalue.puuid))
                return 0;
            break;
        default:
            WIA_WARNING("Pyinsane: WARNING: Unknown var type");
            assert(0);
            return 0;
    }

    CComQIPtr<IWiaPropertyStorage> properties(item);
    hr = properties->WriteMultiple(1, &propspec, &propvalue, property_spec->id);
    if (FAILED(hr)) {
        WIA_WARNING("Pyinsane: WARNING: properties->WriteMultiple() failed");
        return 0;
    }

    return 1;
}

static PyObject *set_property(PyObject *, PyObject *args)
{
    PyObject *capsule;
    PyObject *py_propname;
    PyObject *py_propvalue;
    IWiaItem2 *item;
    const char *propname;
    int i;

    if (!PyArg_ParseTuple(args, "OOO", &capsule, &py_propname, &py_propvalue)) {
        WIA_WARNING("Pyinsane: WARNING: get_sources(): Invalid args");
        return NULL;
    }
    item = capsule2item(capsule);
    if (item == NULL)
        Py_RETURN_FALSE;

    propname = PyUnicode_AsUTF8(py_propname);
    for (i = 0 ; g_wia_all_properties[i].name != NULL ; i++) {
        if (strcmp(g_wia_all_properties[i].name, propname) != 0)
            continue;
        if (!_set_property(item, &g_wia_all_properties[i], py_propvalue)) {
            Py_RETURN_FALSE;
        }
        Py_RETURN_TRUE;
    }

    WIA_WARNING("Pyinsame: WARNING: set_property(): Property not found");
    Py_RETURN_FALSE;
}

struct wia_scan {
    struct wia_source *src;
    IWiaTransfer *transfer;
    PyinsaneWiaTransferCallback *callbacks;
    PyinsaneImageStream *current_stream;
};

static void end_scan(PyObject *capsule)
{
    struct wia_scan *scan;

    scan = (struct wia_scan *)PyCapsule_GetPointer(capsule, WIA_PYCAPSULE_SCAN_NAME);
    if (scan == NULL)
        return;
    scan->transfer->Release();
    delete scan->callbacks;
    free(scan);
}


struct download {
    HANDLE mutex; // because it seems that the callbacks can be called from many threads !
    Py_buffer buffer;
    PyObject *get_data_cb;
    PyObject *end_of_page_cb;
    PyObject *end_of_scan_cb;
    PyThreadState *_save;
};


static void get_data_wrapper(const void *data, int nb_bytes, void *cb_data)
{
    struct download *download = (struct download *)cb_data;
    const char *cdata = (const char *)data; // because Visual C++ says "unknown size" for (void) elements.
    int nb;
    PyObject *arglist;
    PyObject *res;

    WaitForSingleObject(download->mutex, 0);

    PyEval_RestoreThread(download->_save);

    for ( ; nb_bytes > 0 ; nb_bytes -= nb, cdata += nb) {
        nb = WIA_MIN(nb_bytes, download->buffer.len);
        memcpy(download->buffer.buf, cdata, nb);

        arglist = Py_BuildValue("(i)", nb);
        res = PyEval_CallObject(download->get_data_cb, arglist);
        if (res == NULL) {
            WIA_WARNING("Pyinsane: WARNING: Got exception from callback download->get_data_cb !");
        }
        Py_XDECREF(res);
    }

    download->_save = PyEval_SaveThread();

    ReleaseMutex(download->mutex);
}


static void end_of_page_wrapper(void *cb_data)
{
    struct download *download = (struct download *)cb_data;
    PyObject *res;

    WaitForSingleObject(download->mutex, 0);

    PyEval_RestoreThread(download->_save);
    res = PyEval_CallObject(download->end_of_page_cb, NULL);
    if (res == NULL) {
        WIA_WARNING("Pyinsane: WARNING: Got exception from callback download->end_of_page_cb !");
    }
    Py_XDECREF(res);
    download->_save = PyEval_SaveThread();

    ReleaseMutex(download->mutex);
}


static void end_of_scan_wrapper(void *cb_data)
{
    struct download *download = (struct download *)cb_data;
    PyObject *res;

    WaitForSingleObject(download->mutex, 0);

    PyEval_RestoreThread(download->_save);
    res = PyEval_CallObject(download->end_of_scan_cb, NULL);
    if (res == NULL) {
        WIA_WARNING("Pyinsane: WARNING: Got exception from callback download->end_of_scan_cb !");
    }
    Py_XDECREF(res);
    download->_save = PyEval_SaveThread();

    ReleaseMutex(download->mutex);
}


static PyObject *download(PyObject *, PyObject *args)
{
    PyObject *capsule;
    struct download dl_data = { 0 };
    struct wia_scan scan;
    HRESULT hr;
    struct wia_source *src;

    if (!PyEval_ThreadsInitialized()) {
        WIA_WARNING("Python thread not yet initialized ?!");
        PyEval_InitThreads();
    }

    if (!PyArg_ParseTuple(args, "OOOOy*",
                &capsule,
                &dl_data.get_data_cb, &dl_data.end_of_page_cb, &dl_data.end_of_scan_cb,
                &dl_data.buffer
            )) {
        WIA_WARNING("Pyinsane: WARNING: download(): Invalid args");
        return NULL;
    }

    src = (struct wia_source *)PyCapsule_GetPointer(capsule, WIA_PYCAPSULE_SRC_NAME);
    if (src == NULL) {
        WIA_WARNING("Pyinsane: WARNING: wrong param type. Expected a scan source");
        return NULL;
    }

    if (!PyCallable_Check(dl_data.get_data_cb)
            || !PyCallable_Check(dl_data.end_of_page_cb)
            || !PyCallable_Check(dl_data.end_of_scan_cb)) {
        WIA_WARNING("Pyinsane: WARNING: download(): wrong param type. Expected callback(s)");
        Py_RETURN_NONE;
    }

    dl_data.mutex = CreateMutex(NULL, FALSE, NULL);

    hr = src->source->QueryInterface(IID_IWiaTransfer, (void**)&scan.transfer);
    if (FAILED(hr)) {
        WIA_WARNING("source->QueryInterface(WiaTransfer) failed");
        Py_RETURN_NONE;
    }

    scan.callbacks = new PyinsaneWiaTransferCallback(
        get_data_wrapper, end_of_page_wrapper, end_of_scan_wrapper,
        &dl_data
    );

    dl_data._save = PyEval_SaveThread();
    hr = scan.transfer->Download(0, scan.callbacks);
    PyEval_RestoreThread(dl_data._save);

    if (FAILED(hr)) {
        _com_error err(hr);
        LPCTSTR errMsg = err.ErrorMessage();

        WIA_WARNING("Pyinsane: WARNING: source->transfer->Download() failed");

        std::cerr << "Pyinsane: WARNING: source->transfer->Download() failed: " << hr << " ; " << errMsg << std::endl;

        scan.transfer->Release();
    }
    Py_RETURN_NONE;
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
	{"get_properties", get_properties, METH_VARARGS, NULL},
	{"get_sources", get_sources, METH_VARARGS, NULL},
	{"open", open_device, METH_VARARGS, NULL},
	{"download", download, METH_VARARGS, NULL},
	{"set_property", set_property, METH_VARARGS, NULL},
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