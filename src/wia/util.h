#ifndef __PYINSANE_WIA_UTIL_H
#define __PYINSANE_WIA_UTIL_H

#define WIA_COUNT_OF(x) (sizeof(x) / sizeof(x[0]))

#define WIA_WARNING(msg) do { \
        PyErr_WarnEx(NULL, (msg), 1); \
        fprintf(stderr, (msg)); \
        fprintf(stderr, "\n"); \
    } while(0)

#define WIA_MIN(x, y) (((x) < (y)) ? (x) : (y))

#endif