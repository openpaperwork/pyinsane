#include <atlbase.h>
#include <atlconv.h>
#include <comdef.h>

#include "trace.h"
#include "util.h"

#ifdef __cplusplus
extern "C" {
#endif

static volatile HANDLE g_mutex = NULL;
static volatile PyThreadState **g_thread_state = NULL;

static PyObject *g_log_obj = NULL;
static PyObject *g_levels[WIA_MAX_LEVEL + 1] = { 0 }; // pre-allocated strings
static PyObject *g_default_msg = NULL;
static int g_min_level = WIA_DEBUG;

static char g_log_buffer[1024];
static char g_log_buffer2[1024];


void _wia_log(enum wia_log_level lvl, const char *file, int line, LPCSTR fmt, ...)
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
    g_log_buffer[WIA_COUNT_OF(g_log_buffer) - 1] = '\0';

    _snprintf_s(g_log_buffer2, sizeof(g_log_buffer2), _TRUNCATE, "%s(L%d): %s", file, line, g_log_buffer);
    g_log_buffer2[WIA_COUNT_OF(g_log_buffer2) - 1] = '\0';

    if (g_mutex) {
        WaitForSingleObject(g_mutex, 0);
    }
    if (g_thread_state) {
        PyEval_RestoreThread(*((PyThreadState**)g_thread_state));
    }

    msg = PyUnicode_FromString(g_log_buffer2);

    level = g_levels[lvl];

    res = PyObject_CallMethodObjArgs(
            g_log_obj, level, msg != NULL ? msg : g_default_msg, NULL
    );
    if (res != NULL) {
        Py_DECREF(res);
    }
    if (msg != NULL) {
        Py_DECREF(msg);
    }

    if (g_thread_state) {
        *g_thread_state = PyEval_SaveThread();
    }
    if (g_mutex) {
        ReleaseMutex(g_mutex);
    }
}

void _wia_log_hresult(enum wia_log_level lvl, const char *file, int line, HRESULT hr)
{
    const char *msg = NULL;
    LPCTSTR errMsg;

    _com_error err(hr);
    errMsg = err.ErrorMessage();

    msg = CT2CA(errMsg);

    _wia_log(lvl, file, line, "HResult error code 0x%lX: %s", hr, msg);
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
        g_default_msg = PyUnicode_FromString("NULL NULL NULL !!");
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

    Py_RETURN_NONE;
}

void wia_log_set_pythread_state(HANDLE mutex, PyThreadState **thread_state)
{
    g_mutex = mutex;
    g_thread_state = (volatile PyThreadState**)thread_state;
}

#ifdef __cplusplus
}
#endif
