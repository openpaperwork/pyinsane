#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include <Python.h>

#include <Shlwapi.h>

#include "trace.h"
#include "transfer.h"
#include "util.h"


#define TRACE() do { \
        wia_log(WIA_DEBUG, "%s(): L%d", __FUNCTION__, __LINE__); \
    } while(0)


PyinsaneImageStream::PyinsaneImageStream(data_cb getData, void *cbData)
    : mGetData(getData), mCbData(cbData), mRefCount(1), mWritten(0)
{
    TRACE();
}


PyinsaneImageStream::~PyinsaneImageStream()
{
    TRACE();
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Clone(IStream **)
{
    wia_log(WIA_WARNING, "IStream::Clone() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Commit(DWORD)
{
    TRACE();
    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::CopyTo(IStream*, ULARGE_INTEGER, ULARGE_INTEGER*, ULARGE_INTEGER*)
{
    wia_log(WIA_WARNING, "IStream::CopyTo() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::LockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    wia_log(WIA_WARNING, "IStream::LockRegion() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::UnlockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD)
{
    wia_log(WIA_WARNING, "IStream::UnlockRegion() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Read(void *, ULONG, ULONG *)
{
    wia_log(WIA_WARNING, "IStream::Read() not implemented but called !");
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Write(void const* pv, ULONG cb, ULONG* pcbWritten)
{
    if (cb == 0) {
        // Brother MFC-7360N ....
        *pcbWritten = 0;
        return S_OK;
    }
    wia_log(WIA_DEBUG, "%s(): L%d: %lu bytes", __FUNCTION__, __LINE__, cb); \
    mGetData(pv, cb, mCbData);
    TRACE();
    mWritten += cb;
    *pcbWritten = cb;
    return S_OK;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Revert()
{
    wia_log(WIA_WARNING, "IStream::Revert() not implemented but called !");
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
    } else if (mWritten == 0 && dwOrigin == STREAM_SEEK_SET && dlibMove.QuadPart == 0) {
        TRACE();
        plibNewPosition->QuadPart = 0;
        return S_OK;
    }
    wia_log(WIA_WARNING, "IStream::Seek(%lld, %u) not implemented but called !",
            dlibMove.QuadPart, dwOrigin);
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::SetSize(ULARGE_INTEGER newSize)
{
    wia_log(WIA_WARNING, "IStream::SetSize(%llu) not implemented but called !", newSize);
    return E_NOTIMPL;
}


HRESULT STDMETHODCALLTYPE PyinsaneImageStream::Stat(STATSTG *pstatstg, DWORD)
{
    SYSTEMTIME systemTime;
    FILETIME fileTime;

    TRACE();

    GetSystemTime(&systemTime);
    SystemTimeToFileTime(&systemTime, &fileTime);

    memset(pstatstg, 0, sizeof(STATSTG));

    pstatstg->type = STGTY_STREAM;
    pstatstg->mtime = fileTime;
    pstatstg->atime = fileTime;
    pstatstg->grfLocksSupported = LOCK_EXCLUSIVE;
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
        wia_log(WIA_WARNING, "Stream::QueryInterface(): Unknown interface requested");
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
#if 0
    return SHCreateStreamOnFileEx(L"C:\\pouet.bmp", STGM_READWRITE | STGM_CREATE,
        FILE_ATTRIBUTE_NORMAL, TRUE, NULL, ppDestination);
#else
    TRACE();
    *ppDestination = new PyinsaneImageStream(mGetData, mCbData);
    return S_OK;
#endif
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
