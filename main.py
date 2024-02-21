from flask import Flask, request, jsonify
from shm.v2.shm_example import IPC_CREAT, SharedMemory

app = Flask(__name__)


class shmid_ds:
    def __int__(self):
        self.shm_key = -1
        self.shm_shmid = -1
        self.uid = -1
        self.gid = -1
        self.cuid = -1
        self.cgid = -1
        self.mode = 0o000
        self.shm_segsz = -1
        self.shm_lpid = -1
        self.shm_cpid = -1
        self.shm_nattch = -1
        self.shm_atime = -1
        self.shm_dtime = -1
        self.shm_ctime = -1


@app.route("/create", methods=["POST"])
def create():
    data = request.get_json()
    shm = SharedMemory()
    shm_id, err = shm.create(key=int(data["shm_key"]), size=int(data["shm_segsz"]),
                        shm_flags=IPC_CREAT | int("{}".format(data["mode"]), 8))
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    return jsonify({"shm_key": f'{data["shm_key"]}', "shm_shmid": f'{shm_id}'}), 200


@app.route("/remove/<int:key>/<int:shmid>", methods=["DELETE"])
def remove(key, shmid):
    shm = SharedMemory()
    shm.shm_id = shmid
    err = shm.remove()
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    return jsonify({"op": "done"}), 200


@app.route("/stat/<int:key>/<int:shmid>", methods=["GET"])
def stat(key, shmid):
    shm = SharedMemory()
    shm.shm_id = shmid
    shmid_ds_new, err = shm.stat()
    if err != "":
        return jsonify({"err": f'{err}'}), 500

    response = shmid_ds()

    response.shm_key = key
    response.shm_shmid = shmid
    response.uid = shmid_ds_new.contents.shm_perm.uid
    response.gid = shmid_ds_new.contents.shm_perm.gid
    response.cuid = shmid_ds_new.contents.shm_perm.cuid
    response.cgid = shmid_ds_new.contents.shm_perm.cgid
    response.mode = int(oct(shmid_ds_new.contents.shm_perm.mode)[len("0o"):]) % 1000
    response.shm_segsz = shmid_ds_new.contents.shm_segsz
    response.shm_lpid = shmid_ds_new.contents.shm_lpid
    response.shm_cpid = shmid_ds_new.contents.shm_cpid
    response.shm_nattch = shmid_ds_new.contents.shm_nattch
    response.shm_atime = shmid_ds_new.contents.shm_atime
    response.shm_dtime = shmid_ds_new.contents.shm_dtime
    response.shm_ctime = shmid_ds_new.contents.shm_ctime

    return jsonify(response.__dict__), 200


@app.route("/set/<int:key>/<int:shmid>", methods=["PUT"])
def update_perm(key, shmid):
    data = request.get_json()
    uid = int(data["uid"])
    gid = int(data["gid"])
    mode = int("{}".format(data["mode"]), 8)

    shm = SharedMemory()
    shm.shm_id = shmid
    err = shm.set(uid, gid, mode)
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    return jsonify({"op": "done"}), 200


@app.route("/write/<int:key>/<int:shmid>", methods=["POST"])
def write(key, shmid):
    data = request.get_json()
    srt_data = data["data"]

    shm = SharedMemory()
    shm.shm_id = shmid
    _, err = shm.attach()
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    shm.write_data(srt_data)
    err = shm.detach()
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    return jsonify({"op": "done"}), 200


@app.route("/read/<int:key>/<int:shmid>", methods=["GET"])
def read(key, shmid):
    shm = SharedMemory()
    shm.shm_id = shmid
    shmid_ds_new, err = shm.stat()
    if err != "":
        return jsonify({"err": f'{err}'}), 500

    _, err = shm.attach()
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    data = shm.read_data(shmid_ds_new.contents.shm_segsz)
    if err != "":
        return jsonify({"err": f'{err}'}), 500
    return jsonify({"data": data}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=50000)
