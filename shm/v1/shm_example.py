#!/usr/bin/env python
import os
import sys

from ctypes import c_ushort, c_int, c_uint, c_ulong, c_size_t, c_void_p, string_at
from ctypes import CDLL, POINTER, Structure, pointer, create_string_buffer, memmove

libc_so = {"darwin": "libc.dylib", "linux": "/lib/aarch64-linux-gnu/libc.so.6"}[sys.platform]
libc = CDLL(libc_so, use_errno=True, use_last_error=True)

# define consts.
IPC_CREAT = 0o1000
IPC_EXCL = 0o2000
IPC_NOWAIT = 0o4000

IPC_PRIVATE = 0

IPC_RMID = 0
IPC_SET = 1
IPC_STAT = 2
IPC_INFO = 3

SHM_RDONLY = 0o10000
SHM_RND = 0o20000
SHM_REMAP = 0o40000
SHM_EXEC = 0o100000

SHM_LOCK = 11
SHM_UNLOCK = 12

SHM_HUGETLB = 0o4000
SHM_HUGE_2MB = 21 << 26
SHM_HUGE_1GB = 30 << 26
SHM_NORESERVE = 0o10000

SHM_SIZE = 1024
SHM_KEY = 5678

# define structs
if sys.platform == "darwin":
    class ipc_perm(Structure):
        _fields_ = [("uid", c_uint),
                    ("gid", c_uint),
                    ("cuid", c_uint),
                    ("cgid", c_uint),
                    ("mode", c_ushort),
                    ("_seq", c_ushort),
                    ("_key", c_int),
                    ]


    class shmid_ds(Structure):
        _fields_ = [("shm_perm", ipc_perm),
                    ("shm_segsz", c_size_t),
                    ("shm_lpid", c_int),
                    ("shm_cpid", c_int),
                    ("shm_nattch", c_ushort),
                    ("shm_atime", c_ulong),
                    ("shm_dtime", c_ulong),
                    ("shm_ctime", c_ulong),
                    ]

elif sys.platform == "linux":
    class ipc_perm(Structure):
        _fields_ = [("key", c_int),
                    ("uid", c_ushort),
                    ("gid", c_ushort),
                    ("cuid", c_ushort),
                    ("cgid", c_ushort),
                    ("mode", c_ushort),
                    ("seq", c_ushort)
                    ]


    class shmid_ds(Structure):
        _fields_ = [("shm_perm", ipc_perm),
                    ("shm_segsz", c_int),
                    ("shm_atime", c_ulong),
                    ("shm_dtime", c_ulong),
                    ("shm_ctime", c_ulong),
                    ("shm_cpid", c_ushort),
                    ("shm_lpid", c_ushort),
                    ("shm_nattch", c_ushort)
                    ]
else:
    print(f"Unknown platform: {sys.platform}")
    exit(1)


# int shmget(key_t key, size_t size, int shmflg);
shmget = libc.shmget
shmget.restype = c_int
shmget.argtypes = (c_int, c_size_t, c_int)

# void* shmat(int shmid, const void *shmaddr, int shmflg);
shmat = libc.shmat
shmat.restype = c_void_p
shmat.argtypes = (c_int, c_void_p, c_int)

# int shmdt(const void *shmaddr);
shmdt = libc.shmdt
shmdt.restype = c_int
shmdt.argtypes = (c_void_p,)

# int shmctl(int shmid, int cmd, struct shmid_ds *buf);
shmctl = libc.shmctl
shmctl.restype = c_int
shmctl.argtypes = (c_int, c_int, POINTER(shmid_ds))


class SHM:
    size = 0
    shm_id = -1
    at_ptr = None

    def __init__(self, size=0, shm_id=-1, at_ptr=None) -> None:
        self.size = size
        self.shm_id = shm_id
        self.at_ptr = at_ptr

    def create(self, key: int, shm_flags: int) -> int:
        self.shm_id = shmget(key, self.size, shm_flags)
        assert self.shm_id >= 0
        return self.shm_id

    def attach(self):
        self.at_ptr = shmat(self.shm_id, 0, 0)
        assert self.at_ptr is not None
        assert self.at_ptr

    def detach(self):
        if self.at_ptr is not None:
            shmdt(self.at_ptr)
            self.at_ptr = None

    def stat(self):
        shm_ds = shmid_ds()
        result = shmctl(self.shm_id, IPC_STAT, pointer(shm_ds))
        assert result != -1
        return shm_ds

    def set(self, shm_ds: shmid_ds):
        result = shmctl(self.shm_id, IPC_SET, pointer(shm_ds))
        assert result != -1
        return shm_ds

    def write_data(self, data: str):
        # Ensure we're attached to shared memory
        assert self.at_ptr is not None
        # Create a ctypes string buffer from the data
        buf = create_string_buffer(data.encode())
        # Copy the data into shared memory
        memmove(self.at_ptr, buf, len(buf))

    def read_data(self, length) -> str:
        # Ensure we're attached to shared memory
        assert self.at_ptr is not None
        # Read the data from shared memory
        data = string_at(self.at_ptr, length)
        # Return the data as a Python string
        return data.decode()

    def remove(self):
        self.detach()
        shmctl(self.shm_id, IPC_RMID, None)
        self.shm_id = -1


if __name__ == "__main__":
    data = "testdata1"
    myshm = SHM(size=SHM_SIZE)
    myshm.create(key=SHM_KEY, shm_flags=IPC_CREAT | 0o644)
    myshm.attach()

    myshm.write_data(data)
    print(myshm.read_data(len(data)))

    shmds = myshm.stat()
    print(os.getuid())
    print(shmds.shm_perm.uid)

    update_shmds = shmid_ds()
    update_shmds.shm_perm.uid = 0
    update_shmds.shm_perm.gid = 0
    update_shmds.shm_perm.cuid = shmds.shm_perm.cuid
    update_shmds.shm_perm.cgid = shmds.shm_perm.cgid
    update_shmds.shm_perm.mode = shmds.shm_perm.mode
    print(update_shmds.shm_perm.uid)
    myshm.set(update_shmds)

    new_shmds = myshm.stat()
    print(new_shmds.shm_perm.uid)

    update_shmds = shmid_ds()
    update_shmds.shm_perm.uid = os.getuid()
    update_shmds.shm_perm.gid = os.getgid()
    update_shmds.shm_perm.cuid = shmds.shm_perm.cuid
    update_shmds.shm_perm.cgid = shmds.shm_perm.cgid
    update_shmds.shm_perm.mode = shmds.shm_perm.mode
    print(update_shmds.shm_perm.uid)
    myshm.set(update_shmds)

    new_shmds = myshm.stat()
    print(new_shmds.shm_perm.uid)

    myshm.detach()
    print("detached")
    myshm.remove()
    print("removed")

