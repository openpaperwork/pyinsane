#ifndef __PYINSANE_WIA_PROPERTIES_H
#define __PYINSANE_WIA_PROPERTIES_H

#include <Python.h>

#include <windows.h>

struct wia_prop_int {
    int value;
    const char *name;
};

struct wia_prop_clsid {
    CLSID value;
    const char *name;
};

struct wia_property {
    PROPID id;
    VARTYPE vartype;
    const char *name; // NULL == end of list
    int rw;
    const void *possible_values; // points to a (struct wia_prop_*) ; see vartype
    PyObject *(*get_possible_values)(const struct wia_property*);
};

extern const struct wia_property *g_wia_all_properties;

PyObject *int_to_pyobject(const struct wia_property *property, long value);
PyObject *clsid_to_pyobject(const struct wia_property *property, CLSID value);
int pyobject_to_int(const struct wia_property *property_spec, PyObject *pyvalue, int fail_value);
int pyobject_to_clsid(const struct wia_property *property_spec, PyObject *pyvalue, CLSID **out);

#endif