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


PyinsaneImageStream::PyinsaneImageStream(check_still_waiting_for_data_cb *cb, void *cbData)
{
    mCb = cb;
    mCbData = cbData;
}


PyinsaneImageStream::~PyinsaneImageStream()
{
    struct wia_image_stream_el *el, *nel;

    for (el = mFirst ; el != NULL ; el = nel) {
        nel = el->next;
        free(el);
    }
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Clone(IStream **)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Commit(DWORD)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::CopyTo(IStream*, ULARGE_INTEGER, ULARGE_INTEGER*, ULARGE_INTEGER*)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::LockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::UnlockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Read(void* pv, ULONG cb, ULONG* pcbRead)
{
    pv = pv;
    cb = cb;
    pcbRead = pcbRead;
    struct wia_image_stream_el *current;

    std::unique_lock<std::mutex> lock(mMutex);

    if (mFirst == NULL) {
        if (!mCb(this, mCbData)) {
            *pcbRead = 0; // EOF
            mMutex.unlock();
            return S_OK;
        }

        mCondition.wait(lock);
    }

    if (mFirst == NULL) {
        *pcbRead = 0; // EOF
        return S_OK;
    }

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

    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Write(void const* pv, ULONG cb, ULONG* pcbWritten)
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

    std::unique_lock<std::mutex> lock(mMutex);

    if (mLast == NULL) {
        assert(mFirst == NULL);
        mFirst = el;
        mLast = el;
    } else {
        mLast->next = el;
    }

    mCondition.notify_all();
    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Revert()
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Seek(LARGE_INTEGER, DWORD, ULARGE_INTEGER*)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::SetSize(ULARGE_INTEGER)
{
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Stat(STATSTG*, DWORD)
{
    return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE PyinsaneImageStream::QueryInterface(const IID &,void **)
{
    return E_NOTIMPL;
}

ULONG STDMETHODCALLTYPE PyinsaneImageStream::AddRef()
{
    return 0;
}

ULONG STDMETHODCALLTYPE PyinsaneImageStream::Release()
{
    return 0;
}

void STDMETHODCALLTYPE PyinsaneImageStream::wakeUpListeners()
{
    std::unique_lock<std::mutex> lock(mMutex);
    mCondition.notify_all();
}

static check_still_waiting_for_data_cb check_still_waiting;


PyinsaneWiaTransferCallback::PyinsaneWiaTransferCallback()
{
    mRunning = 1;
}


PyinsaneWiaTransferCallback::~PyinsaneWiaTransferCallback()
{
}

void PyinsaneWiaTransferCallback::makeNextStream(std::unique_lock<std::mutex> &lock)
{
    PyinsaneImageStream *stream;

    stream = getCurrentWriteStream();
    if (stream != NULL)
        stream->wakeUpListeners();

    stream = new PyinsaneImageStream(check_still_waiting, this);
    mStreams.push_back(stream);
    mCondition.wait(lock);
}

HRESULT PyinsaneWiaTransferCallback::GetNextStream(
        LONG, BSTR, BSTR, IStream **ppDestination)
{
    std::unique_lock<std::mutex> lock(mMutex);

    if (mStreams.empty()) {
        makeNextStream(lock);
    }
    *ppDestination = getCurrentWriteStream();
    return S_OK;
}


HRESULT PyinsaneWiaTransferCallback::TransferCallback(LONG lFlags, WiaTransferParams *)
{
    std::unique_lock<std::mutex> lock(mMutex);
    if (lFlags == WIA_TRANSFER_MSG_END_OF_TRANSFER) {
        mRunning = 0;
    } else if (lFlags == WIA_TRANSFER_MSG_NEW_PAGE) {
        makeNextStream(lock);
    }
    return S_OK;
}


PyinsaneImageStream *PyinsaneWiaTransferCallback::getCurrentReadStream()
{
    PyinsaneImageStream *stream;

    std::unique_lock<std::mutex> lock(mMutex);

    if (mStreams.empty()) {
        if (mRunning) {
            // Still getting data. Wait for next page
            mCondition.wait(lock);
        }
    }
    if (mStreams.empty()) {
        return NULL;
    }
    stream = mStreams.front();
    return stream;
}


void PyinsaneWiaTransferCallback::popReadStream()
{
    std::unique_lock<std::mutex> lock(mMutex);
    assert(!mStreams.empty());
    delete mStreams.front();
    mStreams.pop_front();
}


PyinsaneImageStream *PyinsaneWiaTransferCallback::getCurrentWriteStream()
{
    PyinsaneImageStream *stream;

    std::unique_lock<std::mutex> lock(mMutex);
    if (mStreams.empty()) {
        return NULL;
    }
    stream = mStreams.back();
    return stream;
}


static int check_still_waiting(void *_img_stream, void *_data)
{
    PyinsaneImageStream *stream = (PyinsaneImageStream *)_img_stream;
    PyinsaneWiaTransferCallback *callbacks = (PyinsaneWiaTransferCallback *)_data;

    callbacks->mMutex.lock();
    if (!callbacks->mRunning) {
        callbacks->mMutex.unlock();
        return 0;
    }
    if (callbacks->getCurrentWriteStream() != stream) {
        callbacks->mMutex.unlock();
        return 0;
    }
    callbacks->mMutex.unlock();
    return 1;
}

HRESULT STDMETHODCALLTYPE PyinsaneWiaTransferCallback::QueryInterface(const IID &,void **)
{
    return E_NOTIMPL;
}

ULONG STDMETHODCALLTYPE PyinsaneWiaTransferCallback::AddRef()
{
    return 0;
}

ULONG STDMETHODCALLTYPE PyinsaneWiaTransferCallback::Release()
{
    return 0;
}
