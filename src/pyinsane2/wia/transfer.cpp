#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include <Python.h>

#include "transfer.h"
#include "util.h"


#define TRACE() do { \
    fprintf(stderr, "DEBUG: L%d : %s\n", __LINE__, __FUNCTION__); \
    fflush(stderr); \
} while(0)
#define TRACE()


PyinsaneImageStream::PyinsaneImageStream(
        data_cb getData, void *cbData
    ) : mGetData(getData), mCbData(cbData), mRefCount(1)
{
    TRACE();
}


PyinsaneImageStream::~PyinsaneImageStream()
{
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


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Read(void *, ULONG, ULONG *)
{
    WIA_WARNING("Pyinsane: WARNING: IStream::Read() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Write(void const* pv, ULONG cb, ULONG* pcbWritten)
{
    TRACE();
    mGetData(pv, cb, mCbData);
    TRACE();
    mWritten += cb;
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
    TRACE();
    mRefCount++;
    return mRefCount;
}


ULONG STDMETHODCALLTYPE PyinsaneImageStream::Release()
{
    TRACE();
    mRefCount--;
    if (mRefCount == 0) {
        TRACE();
        delete this;
    }
    return mRefCount;
}


PyinsaneWiaTransferCallback::PyinsaneWiaTransferCallback(
        data_cb getData, end_of_page_cb eop, end_of_scan_cb eos, void *cbData
    ) : mGetData(getData), mEop(eop), mEos(eos), mCbData(cbData), mRefCount(1)
{
    TRACE();
}


PyinsaneWiaTransferCallback::~PyinsaneWiaTransferCallback()
{
    TRACE();
}

HRESULT PyinsaneWiaTransferCallback::GetNextStream(
        LONG, BSTR, BSTR, IStream **ppDestination)
{
    TRACE();
    *ppDestination = new PyinsaneImageStream(mGetData, mCbData);
    TRACE();
    return S_OK;
}


HRESULT PyinsaneWiaTransferCallback::TransferCallback(LONG, WiaTransferParams *params)
{
    TRACE();
    if (params->lMessage == WIA_TRANSFER_MSG_END_OF_TRANSFER) {
        mEop(mCbData); // mark the current page as finished
    }
    return S_OK;
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
    TRACE();
    mRefCount++;
    return mRefCount;
}

ULONG STDMETHODCALLTYPE PyinsaneWiaTransferCallback::Release()
{
    TRACE();
    mRefCount--;
    if (mRefCount == 0) {
        TRACE();
        delete this;
    }
    return mRefCount;
}
