#include "trace.h"


static PyObject *g_log_obj = NULL;
static PyObject *g_levels[WIA_MAX_LEVEL + 1] = { 0 }; // pre-allocated strings
static int g_min_level = WIA_DEBUG;
static char g_log_buffer[1024];


void wia_log(enum wia_log_level lvl, LPCSTR fmt, ...)
{
    PyObject *res;
    PyObject *level;
    PyObject *msg;
    va_list args;
    va_start(args, fmt);

    if (g_log_obj == NULL || lvl < g_min_level) {
        return;
    }

    memset(g_log_buffer, 0, sizeof(g_log_buffer));
    vsnprintf_s(g_log_buffer, _countof(g_log_buffer), _TRUNCATE, fmt, args);
    msg = PyUnicode_FromString(g_log_buffer);

    level = g_levels[lvl];

    res = PyObject_CallMethodObjArgs(g_log_obj, level, NULL);
    if (res != NULL) {
        Py_DECREF(res);
    }
}

PyObject *register_logger(PyObject *, PyObject *args)
{
    PyObject *log_obj = NULL;
    int min_log_level = WIA_DEBUG;

    if (g_levels[0] == NULL) {
        g_levels[WIA_DEBUG] = PyUnicode_FromString("debug");
        g_levels[WIA_INFO] = PyUnicode_FromString("info");
        g_levels[WIA_WARNING] = PyUnicode_FromString("warning");
        g_levels[WIA_ERROR] = PyUnicode_FromString("error");
    }

    if (!PyArg_ParseTuple(args, "iO", &min_log_level, &log_obj)) {
        return NULL;
    }

    if (g_log_obj != NULL) {
        Py_DECREF(g_log_obj);
        g_log_obj = NULL;
    }

    g_min_level = min_log_level;
    if (log_obj != NULL) {
        Py_INCREF(log_obj);
        g_log_obj = log_obj;
    }

    Py_INCREF(Py_None);
    return Py_None;
}
