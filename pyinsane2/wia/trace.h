#ifndef __PYINSANE_WIA_TRACE_H
#define __PYINSANE_WIA_TRACE_H

/* #define ENABLE_STDIO */

#ifdef ENABLE_STDIO
#include <stdio.h>
#endif

#include <wtypes.h>
#include <winerror.h>

#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

enum wia_log_level {
    WIA_DEBUG,
    WIA_INFO,
    WIA_WARNING,
    WIA_ERROR,
    WIA_MAX_LEVEL = WIA_ERROR,
};


#ifdef ENABLE_STDIO

#define wia_log(lvl, fmt, ...) do { \
    fprintf(stderr, fmt, __VA_ARGS__); \
    fprintf(stderr, "\n"); \
    _wia_log(lvl, __FILE__, __LINE__, fmt, __VA_ARGS__); \
} while(0)

#else

#define wia_log(lvl, fmt, ...) _wia_log(lvl, __FILE__, __LINE__, fmt, __VA_ARGS__);

#endif

#define wia_log_hresult(lvl, hr) _wia_log_hresult(lvl, __FILE__, __LINE__, hr)

void _wia_log(enum wia_log_level lvl, const char *file, int line, LPCSTR fmt, ...);
void _wia_log_hresult(enum wia_log_level lvl, const char *file, int line, HRESULT hr);

PyObject *register_logger(PyObject *, PyObject *args);
void wia_log_set_pythread_state(HANDLE mutex, PyThreadState **thread_state);

#ifdef __cplusplus
}
#endif

#endif
