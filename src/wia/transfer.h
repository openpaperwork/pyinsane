#ifndef __PYINSANE_WIA_TRANSFER_H
#define __PYINSANE_WIA_TRANSFER_H

#include <list>
#include <mutex>
#include <thread>

#include <windows.h>
#include <atlbase.h>
#include <wia.h>
#include <Sti.h>

typedef int (check_still_waiting_for_data_cb)(void *img_stream, void *data);

class PyinsaneImageStream : public IStream
{
public:
    PyinsaneImageStream(check_still_waiting_for_data_cb *cb, void *cbData);
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

    virtual void wakeUpListeners();

private:
    check_still_waiting_for_data_cb *mCb;
    void *mCbData;

    std::mutex mMutex;
    std::condition_variable mCondition;

    struct wia_image_stream_el *mFirst;
    struct wia_image_stream_el *mLast;
};

class PyinsaneWiaTransferCallback : public IWiaTransferCallback
{
public:
    PyinsaneWiaTransferCallback();
    ~PyinsaneWiaTransferCallback();

    // interface methods
    virtual HRESULT GetNextStream(LONG lFlags, BSTR bstrItemName, BSTR bstrFullItemName, IStream **ppDestination);
    virtual HRESULT TransferCallback(LONG lFlags, WiaTransferParams *pWiaTransferParams);
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(const IID &,void **);
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

    // Pyinsane methods
    PyinsaneImageStream *getCurrentReadStream();
    void popReadStream();
    PyinsaneImageStream *getCurrentWriteStream();
    int mRunning;
    std::mutex mMutex;

private:
    void makeNextStream(std::unique_lock<std::mutex> &lock);

    std::condition_variable mCondition;

    std::list<PyinsaneImageStream *> mStreams;
};

#endif