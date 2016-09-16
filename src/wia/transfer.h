#ifndef __PYINSANE_WIA_TRANSFER_H
#define __PYINSANE_WIA_TRANSFER_H

#include <mutex>
#include <thread>

#include <windows.h>
#include <atlbase.h>
#include <wia.h>
#include <Sti.h>

typedef int (*check_still_waiting_for_data_cb)(void *data);

class WiaImageStream : public IStream
{
public:
    WiaImageStream(check_still_waiting_for_data_cb cb, void *cbData);
    ~WiaImageStream();

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

private:
    check_still_waiting_for_data_cb mCb;
    void *mCbData;

    std::unique_lock<std::mutex> mMutex;
    std::condition_variable mCondition;

    struct wia_image_stream_el *mFirst;
    struct wia_image_stream_el *mLast;
};

#endif