#ifndef __PYINSANE_WIA_TRACE_H
#define __PYINSANE_WIA_TRACE_H

#include <wtypes.h>

#include <Python.h>

enum wia_log_level {
    WIA_DEBUG,
    WIA_INFO,
    WIA_WARNING,
    WIA_ERROR,
    WIA_MAX_LEVEL = WIA_ERROR,
};

void wia_log(enum wia_log_level lvl, LPCSTR fmt, ...);
PyObject *register_logger(PyObject *, PyObject *args);

#endif
