# Shared Memory in python

-----------------

A python implementation to perform operations on a Shared Memory. While it is conventional to use the System V library,
we had a requirement to change the permissions of a Shared memory segment on-demand which is not supported by the
System V library. In this repository, the Shared memory interactions are implemented in C code and accessed them in 
python application using the CTypes library.

### The following Shared memory operations are supported:

- **Create** - Used to create a Shared Memory segment for a given size and key. Returns SHMID.
- **Attach** - Attaches to the Shared Memory segment identified by the given SHMID. Returns access pointer.
- **Detach** - Detaches the Shared Memory segment identified by the given SHMID.
- **Stat** - Returns Shared Memory info (shmid_ds)
- **Set** - Updates UID, GID and MODE of a Shared Memory segment identified by the given SHMID.
- **Remove** - Detaches the Shared Memory segment identified by the given SHMID.

Refer [shm/v2/shm_example.py](shm%2Fv2%2Fshm_example.py) for implementation details.

### Usage

The aforementioned operation are exposed as the following API endpoints.

Note: The Read and Write API implementation user Attach and Detach internally.

- **Create**: 
  - API: POST `http://localhost:50000/create`
    - Sample Request:
      ```
        {
          "shm_key": 5679,
          "shm_segsz": 1024,
          "mode":666
        }
        ```
    - Sample Response:
      ```
        {
          "shm_key": "5679",
          "shm_shmid": "0"
        }
      ```
- **Stat**:
    - API: GET `http://localhost:50000/stat/<key>/<shmid>`
        - Sample Response:
          ```
            {
              "cgid": 999,
              "cuid": 999,
              "gid": 999,
              "mode": 666,
              "shm_atime": 1708474369,
              "shm_cpid": 22,
              "shm_ctime": 1708474379,
              "shm_dtime": 1708474364,
              "shm_key": 5679,
              "shm_lpid": 0,
              "shm_nattch": 5,
              "shm_segsz": 1024,
              "shm_shmid": 0,
              "uid": 999
            }
          ```
- **Write**:
    - API: POST `http://localhost:50000/write/<key>/<shmid>`
        - Sample Request:
          ```
            {
              "data": "testdata2"
            }
          ```
        - Sample Response:
          ```
            {
              "op": "done"
            }
          ```
- **Read**:
    - API: GET `http://localhost:50000/read/<key>/<shmid>`
        - Sample Response:
          ```
            {
              "data": "testdata2"
            }
          ```
- **Set**:
    - API: PUT `http://localhost:50000/set/<key>/<shmid>`
        - Sample Request:
          ```
            {
              "uid": 999,
              "gid": 999,
              "mode": 600
            }
            ```
        - Sample Response:
          ```
            {
              "op": "done"
            }
          ```
- **Remove**:
    - API: DELETE `http://localhost:50000/remove/<key>/<shmid>`
        - Sample Response:
          ```
            {
              "op": "done"
            }

### Deployment

- Run locally: 
  - `pip install -r requirements.txt`
  - `make run-python`
- Run as container: 
  - `make run-container`

### Tested environment

- **Arch**: ARM64
- **Platform**: Darwin, Linux
- **GCC Version**: C++17
- **Python Version**: 3.9

