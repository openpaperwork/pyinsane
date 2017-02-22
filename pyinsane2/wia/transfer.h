#ifndef __PYINSANE_WIA_TRANSFER_H
#define __PYINSANE_WIA_TRANSFER_H

#include <list>

#include <windows.h>
#include <wia.h>
#include <Sti.h>

typedef void (*data_cb)(const void *data, int nb_bytes, void *cb_data);
typedef void (*end_of_page_cb)(void *cb_data);
typedef void (*end_of_scan_cb)(void *cb_data);

class PyinsaneImageStream : public IStream
{
public:
    PyinsaneImageStream(data_cb getData, void *cbData);
    ~PyinsaneImageStream();

    virtual HRESULT STDMETHODCALLTYPE Clone(IStream **);
    virtual HRESULT STDMETHODCALLTYPE Commit(DWORD);
    virtual HRESULT STDMETHODCALLTYPE CopyTo(IStream*, ULARGE_INTEGER, ULARGE_INTEGER*, ULARGE_INTEGER*);
    virtual HRESULT STDMETHODCALLTYPE LockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD);
    virtual HRESULT STDMETHODCALLTYPE Read(void* pv, ULONG cb, ULONG* pcbRead);
    virtual HRESULT STDMETHODCALLTYPE Revert();
    virtual HRESULT STDMETHODCALLTYPE Seek(LARGE_INTEGER liDistanceToMove, DWORD dwOrigin,
            ULARGE_INTEGER* lpNewFilePointer);
    virtual HRESULT STDMETHODCALLTYPE SetSize(ULARGE_INTEGER);
    virtual HRESULT STDMETHODCALLTYPE Stat(STATSTG* pStatstg, DWORD grfStatFlag);
    virtual HRESULT STDMETHODCALLTYPE UnlockRegion(ULARGE_INTEGER, ULARGE_INTEGER, DWORD);
    virtual HRESULT STDMETHODCALLTYPE Write(void const* pv, ULONG cb, ULONG* pcbWritten);
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(const IID &,void **);
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

private:
    unsigned long long mWritten;
    int mRefCount;
    data_cb mGetData;
    void *mCbData;
};

class PyinsaneWiaTransferCallback : public IWiaTransferCallback
{
public:
    PyinsaneWiaTransferCallback(data_cb getData, end_of_page_cb eop, end_of_scan_cb eos, void *cbData);
    ~PyinsaneWiaTransferCallback();

    // interface methods
    virtual HRESULT STDMETHODCALLTYPE GetNextStream(LONG lFlags, BSTR bstrItemName, BSTR bstrFullItemName, IStream **ppDestination);
    virtual HRESULT STDMETHODCALLTYPE TransferCallback(LONG lFlags, WiaTransferParams *pWiaTransferParams);
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void **ppvObject);
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

private:
    data_cb mGetData;
    end_of_page_cb mEop;
    end_of_scan_cb mEos;
    void *mCbData;
    int mRefCount;
};

#endif