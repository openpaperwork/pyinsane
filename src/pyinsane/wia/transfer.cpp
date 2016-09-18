#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include <Python.h>

#include "transfer.h"
#include "util.h"


//#define TRACE() do { \
//    fprintf(stderr, "DEBUG: L%d : %s\n", __LINE__, __FUNCTION__); \
//    fflush(stderr); \
//} while(0)
#define TRACE()


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
    mWritten = 0;
    mRead = 0;
    mFirst = NULL;
    mLast = NULL;
    TRACE();
}


PyinsaneImageStream::~PyinsaneImageStream()
{
    struct wia_image_stream_el *el, *nel;

    assert(mWritten == mRead); // cancel is not yet supported, so ...

    TRACE();
    for (el = mFirst ; el != NULL ; el = nel) {
        nel = el->next;
        free(el);
    }
    TRACE();
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Clone(IStream **)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::Clone() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Commit(DWORD)
{
    TRACE();
    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::CopyTo(IStream*, ULARGE_INTEGER, ULARGE_INTEGER*, ULARGE_INTEGER*)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::CopyTo() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::LockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::LockRegion() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::UnlockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::UnlockRegion() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Read(void* pv, ULONG cb, ULONG* pcbRead)
{
    pv = pv;
    cb = cb;
    pcbRead = pcbRead;
    struct wia_image_stream_el *current;

    std::unique_lock<std::mutex> lock(mMutex);

    TRACE();

    if (mFirst == NULL) {
        if (!mCb(this, mCbData)) {
            *pcbRead = 0; // EOF
            mMutex.unlock();
            TRACE();
            return S_OK;
        }
        TRACE();
        mCondition.wait(lock);
    }

    if (mFirst == NULL) {
        *pcbRead = 0; // EOF
        TRACE();
        return S_OK;
    }

    current = mFirst;

    TRACE();

    *pcbRead = WIA_MIN(current->nb_bytes, cb);
    assert(*pcbRead > 0); // would mean EOF otherwise
    memcpy(pv, current->data, *pcbRead);
    mRead += *pcbRead;

    TRACE();

    if (current->nb_bytes == *pcbRead) {
        TRACE();
        // this element has been fully consumed
        if (mLast == mFirst) {
            mLast = NULL;
            mFirst = NULL;
        } else {
            mFirst = mFirst->next;
        }
        free(current);
        TRACE();
    } else {
        TRACE();
        // there is remaining data in the element
        current->data += *pcbRead;
        current->nb_bytes -= *pcbRead;
    }

    TRACE();

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

    TRACE();

    el = (struct wia_image_stream_el *)malloc(sizeof(struct wia_image_stream_el) + cb);
    memcpy(el->odata, pv, cb);
    el->data = el->odata;
    el->nb_bytes = cb;
    el->next = NULL;

    TRACE();

    std::unique_lock<std::mutex> lock(mMutex);

    TRACE();

    if (mLast == NULL) {
        TRACE();
        assert(mFirst == NULL);
        mFirst = el;
        mLast = el;
    } else {
        TRACE();
        mLast->next = el;
        mLast = el;
    }

    mWritten += cb;
    mCondition.notify_all();
    TRACE();
    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Revert()
{
    WIA_WARNING("Pyinsane: WARNING: IStream::Revert() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Seek(
        LARGE_INTEGER dlibMove, DWORD dwOrigin, ULARGE_INTEGER *plibNewPosition
    )
{
    TRACE();
    if (dwOrigin == STREAM_SEEK_END && dlibMove.QuadPart == 0) {
        TRACE();
        plibNewPosition->QuadPart = mWritten;
        return S_OK;
    }
    WIA_WARNING("Pyinsane: WARNING: IStream::Seek() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::SetSize(ULARGE_INTEGER)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::SetSize() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Stat(STATSTG *pstatstg, DWORD)
{
    TRACE();
    memset(pstatstg, 0, sizeof(STATSTG));
    pstatstg->type = STGTY_STREAM;
    pstatstg->cbSize.QuadPart = mWritten;
    pstatstg->clsid = CLSID_NULL;
    return S_OK;
}

HRESULT STDMETHODCALLTYPE PyinsaneImageStream::QueryInterface(REFIID riid, void **ppvObject)
{
    assert(NULL != ppvObject);

    TRACE();

    if (IsEqualIID(riid, IID_IUnknown))
    {
        *ppvObject = static_cast<IUnknown*>(this);
    }
    else if (IsEqualIID(riid, IID_IStream))
    {
        *ppvObject = static_cast<IStream*>(this);
    }
    else
    {
        *ppvObject = NULL;
        TRACE();
        return E_NOINTERFACE;
    }

    TRACE();

    // Increment the reference count before we return the interface
    reinterpret_cast<IUnknown*>(*ppvObject)->AddRef();
    return S_OK;
}

ULONG STDMETHODCALLTYPE PyinsaneImageStream::AddRef()
{
    //WIA_WARNING("Pyinsane: WARNING: IStream::AddRef() not implemented but called !");
    TRACE();
    return 0;
}

ULONG STDMETHODCALLTYPE PyinsaneImageStream::Release()
{
    //WIA_WARNING("Pyinsane: WARNING: IStream::Release() not implemented but called !");
    TRACE();
    return 0;
}

void STDMETHODCALLTYPE PyinsaneImageStream::wakeUpListeners()
{
    TRACE();
    std::unique_lock<std::mutex> lock(mMutex);
    mCondition.notify_all();
    TRACE();
}

static check_still_waiting_for_data_cb check_still_waiting;


PyinsaneWiaTransferCallback::PyinsaneWiaTransferCallback()
{
    TRACE();
    mRunning = 1;
}


PyinsaneWiaTransferCallback::~PyinsaneWiaTransferCallback()
{
    TRACE();
}

void PyinsaneWiaTransferCallback::wakeUpReader()
{
    PyinsaneImageStream *stream;

    if (!mStreams.empty()) {
        TRACE();
        stream = mStreams.back();
        stream->wakeUpListeners();
    }
}

void PyinsaneWiaTransferCallback::makeNextStream()
{
    PyinsaneImageStream *stream;

    TRACE();
    wakeUpReader();

    TRACE();
    stream = new PyinsaneImageStream(check_still_waiting, this);
    mStreams.push_back(stream);
    mCondition.notify_all();
    TRACE();
}

HRESULT PyinsaneWiaTransferCallback::GetNextStream(
        LONG, BSTR, BSTR, IStream **ppDestination)
{
    TRACE();
    std::unique_lock<std::mutex> lock(mMutex);
    if (mStreams.empty()) {
        TRACE();
        makeNextStream();
    }
    TRACE();
    *ppDestination = mStreams.back();
    TRACE();
    return S_OK;
}


HRESULT PyinsaneWiaTransferCallback::TransferCallback(LONG, WiaTransferParams *params)
{
    TRACE();
    std::unique_lock<std::mutex> lock(mMutex);
    TRACE();
    if (params->lMessage == WIA_TRANSFER_MSG_END_OF_TRANSFER) {
        TRACE();
        mRunning = 0;
        wakeUpReader();
    } else if (params->lMessage == WIA_TRANSFER_MSG_NEW_PAGE) {
        TRACE();
        makeNextStream();
    }
    TRACE();
    return S_OK;
}


PyinsaneImageStream *PyinsaneWiaTransferCallback::getCurrentReadStream()
{
    PyinsaneImageStream *stream;

    TRACE();
    std::unique_lock<std::mutex> lock(mMutex);

    if (mStreams.empty()) {
        TRACE();
        if (mRunning) {
            // Still getting data. Wait for next page
            TRACE();
            mCondition.wait(lock);
        }
    }
    TRACE();
    if (mStreams.empty()) {
        TRACE();
        return NULL;
    }
    TRACE();
    stream = mStreams.front();
    return stream;
}


void PyinsaneWiaTransferCallback::popReadStream()
{
    TRACE();
    std::unique_lock<std::mutex> lock(mMutex);
    assert(!mStreams.empty());
    TRACE();
    delete mStreams.front();
    mStreams.pop_front();
    TRACE();
}


PyinsaneImageStream *PyinsaneWiaTransferCallback::getCurrentWriteStream()
{
    PyinsaneImageStream *stream;

    TRACE();
    if (mStreams.empty()) {
        TRACE();
        return NULL;
    }
    TRACE();
    stream = mStreams.back();
    TRACE();
    return stream;
}


static int check_still_waiting(void *_img_stream, void *_data)
{
    PyinsaneImageStream *stream = (PyinsaneImageStream *)_img_stream;
    PyinsaneWiaTransferCallback *callbacks = (PyinsaneWiaTransferCallback *)_data;

    TRACE();
    callbacks->mMutex.lock();
    if (!callbacks->mRunning) {
        TRACE();
        callbacks->mMutex.unlock();
        return 0;
    }
    TRACE();
    if (callbacks->getCurrentWriteStream() != stream) {
        TRACE();
        callbacks->mMutex.unlock();
        return 0;
    }
    TRACE();
    callbacks->mMutex.unlock();
    return 1;
}


HRESULT STDMETHODCALLTYPE PyinsaneWiaTransferCallback::QueryInterface(REFIID riid, void **ppvObject)
{
    assert(NULL != ppvObject);

    TRACE();
    if (IsEqualIID(riid, IID_IUnknown))
    {
        TRACE();
        *ppvObject = static_cast<IUnknown*>(this);
    }
    else if (IsEqualIID( riid, IID_IWiaTransferCallback ))
    {
        TRACE();
        *ppvObject = static_cast<IWiaTransferCallback*>(this);
    }
    else
    {
        TRACE();
        *ppvObject = NULL;
        return E_NOINTERFACE;
    }

    TRACE();
    // Increment the reference count before we return the interface
    reinterpret_cast<IUnknown*>(*ppvObject)->AddRef();
    return S_OK;
}


ULONG STDMETHODCALLTYPE PyinsaneWiaTransferCallback::AddRef()
{
    //WIA_WARNING("Pyinsane: WARNING: WiaTransferCallback::AddRef() not implemented but called !");
    TRACE();
    return 0;
}

ULONG STDMETHODCALLTYPE PyinsaneWiaTransferCallback::Release()
{
    //WIA_WARNING("Pyinsane: WARNING: WiaTransferCallback::Release() not implemented but called !");
    TRACE();
    return 0;
}
