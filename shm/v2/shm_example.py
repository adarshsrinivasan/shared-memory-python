#!/usr/bin/env python
import os
import sys

from ctypes import c_ushort, c_int, c_uint, c_ulong, c_size_t, c_void_p, string_at, c_char, c_long, cast
from ctypes import CDLL, POINTER, Structure, pointer, create_string_buffer, memmove

# define constants
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

# load c library
lib = CDLL(f"./shm_lib_{sys.platform}.so")


# define structs
class ipc_perm_new(Structure):
    _fields_ = [("uid", c_uint),
                ("gid", c_uint),
                ("cuid", c_uint),
                ("cgid", c_uint),
                ("mode", c_ushort),
                ]


class shmid_ds_new(Structure):
    _fields_ = [("shm_perm", ipc_perm_new),
                ("shm_segsz", c_size_t),
                ("shm_lpid", c_int),
                ("shm_cpid", c_int),
                ("shm_nattch", c_ushort),
                ("shm_atime", c_long),
                ("shm_dtime", c_long),
                ("shm_ctime", c_long),
                ]


# Define methods

# int Create(key_t key, size_t size, int flags);
lib.Create.argtypes = [c_int, c_size_t, c_int]
lib.Create.restype = c_int

# void* Attach(int shmid);
lib.Attach.argtypes = [c_int]
lib.Attach.restype = c_void_p

# int Detach(void* ptr);
lib.Detach.argtypes = [c_void_p]
lib.Detach.restype = c_int

# struct shmid_ds_new* Stat(int shmid);
lib.Stat.argtypes = [c_int]
lib.Stat.restype = POINTER(shmid_ds_new)

# int Set(int shmid, uid_t uid, gid_t gid, mode_t mode);
lib.Set.argtypes = [c_int, c_uint, c_uint, c_ushort]
lib.Set.restype = c_int

# int Remove(int shmid);
lib.Remove.argtypes = [c_int]
lib.Remove.restype = c_int

# void Write(void* ptr, const char* str);
lib.Write.argtypes = [c_void_p, POINTER(c_char)]
lib.Write.restype = None

# char* Read(void* ptr);
lib.Read.argtypes = [c_void_p]
lib.Read.restype = POINTER(c_char)


class SharedMemory:
    def __init__(self) -> None:
        self.size = 0
        self.shm_id = -1
        self.key = -1
        self.at_ptr = None

    def create(self, key: int, size: int, shm_flags: int):
        self.size = size
        self.key = key
        self.shm_id = lib.Create(key, size, shm_flags)
        if self.shm_id < 0:
            err = f"Error: exception while create operation. shm_id: {self.shm_id}"
            print(f"{err}\n")
            return self.shm_id, err
        assert self.shm_id >= 0
        return self.shm_id, ""

    def attach(self):
        self.at_ptr = lib.Attach(self.shm_id)
        if self.at_ptr is None:
            err = f"Error: exception while attach operation. at_ptr: None"
            print(f"{err}\n")
            return self.at_ptr, err
        return self.at_ptr, ""

    def detach(self):
        if self.at_ptr is not None:
            ret = lib.Detach(self.at_ptr)
            if self.at_ptr is None:
                err = f"Error: exception while detach operation. ret: {ret}"
                print(f"{err}\n")
                return err
            self.at_ptr = None
            return ""

    def stat(self):
        stat_res = lib.Stat(self.shm_id)
        if stat_res is None:
            err = f"Error: exception while stat operation. stat_res: None"
            print(f"{err}\n")
            return stat_res, err
        return stat_res, ""

    def set(self, uid: int, gid: int, mode: int):
        set_res = lib.Set(self.shm_id, uid, gid, mode)
        if set_res < 0:
            err = f"Error: exception while set operation. set_res: {set_res}"
            print(f"{err}\n")
            return err
        return ""

    def write_data(self, data: str):
        assert self.at_ptr is not None
        buf = create_string_buffer(data.encode())
        # memmove(self.at_ptr, buf, len(buf))
        lib.Write(self.at_ptr, buf)

    def read_data(self, length) -> str:
        assert self.at_ptr is not None
        # data = string_at(self.at_ptr, length)
        data = string_at(lib.Read(self.at_ptr), length).decode('utf-8').split('\x00')[0]
        return data

    def remove(self):
        self.detach()
        rmv_res = lib.Remove(self.shm_id)
        if rmv_res < 0:
            err = f"Error: exception while remove operation. rmv_res: {rmv_res}"
            print(f"{err}\n")
            return err
        self.shm_id = -1
        return ""


def Test():
    data = "testdata1"
    myshm = SharedMemory()
    shm_id = myshm.create(key=SHM_KEY, size=SHM_SIZE, shm_flags=IPC_CREAT | 0o644)
    myshm.attach()

    shmid_ds, _  = myshm.stat()
    print("\nshmid_ds Information:")
    print(f"key: {SHM_KEY}")
    print(f"shmid: {shm_id}")
    print(f"Mode: {shmid_ds.contents.shm_perm.mode}")
    print(f"UID: {shmid_ds.contents.shm_perm.uid}")
    print(f"GID: {shmid_ds.contents.shm_perm.gid}")
    print(f"Size: {shmid_ds.contents.shm_segsz} bytes")
    print(f"Last attach time: {shmid_ds.contents.shm_atime}")
    print(f"Last detach time: {shmid_ds.contents.shm_dtime}")
    print(f"Last change time: {shmid_ds.contents.shm_ctime}")
    print(f"Number of attaches: {shmid_ds.contents.shm_nattch}\n")

    myshm.write_data(data)
    print(myshm.read_data(len(data)))

    myshm.set(0, 0, 0o666)

    shmid_ds_new1, _  = myshm.stat()
    print("\nshmid_ds Information:")
    print(f"key: {SHM_KEY}")
    print(f"shmid: {shm_id}")
    print(f"Mode: {shmid_ds_new1.contents.shm_perm.mode}")
    print(f"UID: {shmid_ds_new1.contents.shm_perm.uid}")
    print(f"GID: {shmid_ds_new1.contents.shm_perm.gid}")
    print(f"Size: {shmid_ds_new1.contents.shm_segsz} bytes")
    print(f"Last attach time: {shmid_ds_new1.contents.shm_atime}")
    print(f"Last detach time: {shmid_ds_new1.contents.shm_dtime}")
    print(f"Last change time: {shmid_ds_new1.contents.shm_ctime}")
    print(f"Number of attaches: {shmid_ds_new1.contents.shm_nattch}\n")

    myshm.set(shmid_ds.contents.shm_perm.uid, shmid_ds.contents.shm_perm.gid, shmid_ds.contents.shm_perm.mode)

    shmid_ds_new2, _  = myshm.stat()
    print("\nshmid_ds Information:")
    print(f"key: {SHM_KEY}")
    print(f"shmid: {shm_id}")
    print(f"Mode: {shmid_ds_new2.contents.shm_perm.mode}")
    print(f"UID: {shmid_ds_new2.contents.shm_perm.uid}")
    print(f"GID: {shmid_ds_new2.contents.shm_perm.gid}")
    print(f"Size: {shmid_ds_new2.contents.shm_segsz} bytes")
    print(f"Last attach time: {shmid_ds_new2.contents.shm_atime}")
    print(f"Last detach time: {shmid_ds_new2.contents.shm_dtime}")
    print(f"Last change time: {shmid_ds_new2.contents.shm_ctime}")
    print(f"Number of attaches: {shmid_ds_new2.contents.shm_nattch}\n")

    myshm.detach()
    print("detached")
    myshm.remove()
    print("removed")
