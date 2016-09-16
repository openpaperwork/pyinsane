#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "transfer.h"
#include "util.h"

struct wia_image_stream_el {
    char *data; // points to somewhere in the odata buffer
    unsigned long nb_bytes; // remaining number of bytes between 'data' and the end of the buffer 'odata'

    struct wia_image_stream_el *next;

    char odata[]; // original data, as written by the source
};

WiaImageStream::WiaImageStream(check_still_waiting_for_data_cb cb, void *cbData)
{
    mCb = cb;
    mCbData = cbData;
}

WiaImageStream::~WiaImageStream()
{
    struct wia_image_stream_el *el, *nel;

    for (el = mFirst ; el != NULL ; el = nel) {
        nel = el->next;

        free(el);
    }
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Clone(IStream **)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Commit(DWORD)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::CopyTo(IStream*, ULARGE_INTEGER, ULARGE_INTEGER*, ULARGE_INTEGER*)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::LockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::UnlockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Read(void* pv, ULONG cb, ULONG* pcbRead)
{
    pv = pv;
    cb = cb;
    pcbRead = pcbRead;
    struct wia_image_stream_el *current;

    mMutex.lock();

    if (mFirst == NULL) {
        if (!mCb(mCbData)) {
            *pcbRead = 0; // EOF
            mMutex.unlock();
            return S_OK;
        }

        mCondition.wait(mMutex);
    }

    assert(mFirst != NULL);

    current = mFirst;

    *pcbRead = WIA_MIN(current->nb_bytes, cb);
    assert(*pcbRead > 0); // would mean EOF otherwise
    memcpy(pv, current->data, *pcbRead);

    if (current->nb_bytes == *pcbRead) {
        // this element has been fully consumed
        mFirst = mFirst->next;

        free(current);
    } else {
        // there is remaining data in the element
        current->data += *pcbRead;
        current->nb_bytes -= *pcbRead;
    }

    mMutex.unlock();

    return S_OK;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Write(void const* pv, ULONG cb, ULONG* pcbWritten)
{
    pv = pv;
    cb = cb;
    pcbWritten = pcbWritten;
    struct wia_image_stream_el *el;

    if (cb == 0) {
        return S_OK;
    }

    el = (struct wia_image_stream_el *)malloc(sizeof(struct wia_image_stream_el) + cb);
    memcpy(el->odata, pv, cb);
    el->data = el->odata;
    el->nb_bytes = cb;
    el->next = NULL;

    mMutex.lock();

    if (mLast == NULL) {
        assert(mFirst == NULL);
        mFirst = el;
        mLast = el;
    } else {
        mLast->next = el;
    }

    mCondition.notify_all();
    mMutex.unlock();

    return S_OK;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Revert()
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Seek(LARGE_INTEGER, DWORD, ULARGE_INTEGER*)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::SetSize(ULARGE_INTEGER)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE WiaImageStream::Stat(STATSTG*, DWORD)
{
    return E_NOTIMPL;
}