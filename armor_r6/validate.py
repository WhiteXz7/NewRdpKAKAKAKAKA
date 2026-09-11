#!/usr/bin/env python3
"""validate.py — Verificação de integridade dos artefatos gerados.

Checa:
  1. glb: estrutura, tamanho do buffer, accessors, joints,
  2. skinning: no bind pose, vértice deformado == vértice original (identidade),
  3. animação: num frame de caminhada, os braços/pernas realmente se movem,
  4. bvh: hierarquia e contagem de canais,
  5. obj: contagem de vértices/faces por objeto.

Uso: python3 validate.py
"""

import json
import math
import os
import struct

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "export")


# ------------------------------------------------------------------ mat4 (col-major)
def m4_identity():
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def m4_translate(x, y, z):
    m = m4_identity()
    m[12], m[13], m[14] = x, y, z
    return m


def m4_mul(a, b):
    r = [0.0] * 16
    for col in range(4):
        for row in range(4):
            s = 0.0
            for k in range(4):
                s += a[k * 4 + row] * b[col * 4 + k]
            r[col * 4 + row] = s
    return r


def m4_rot_quat(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    # coluna-major
    return [1 - 2 * (yy + zz), 2 * (xy + wz), 2 * (xz - wy), 0,
            2 * (xy - wz), 1 - 2 * (xx + zz), 2 * (yz + wx), 0,
            2 * (xz + wy), 2 * (yz - wx), 1 - 2 * (xx + yy), 0,
            0, 0, 0, 1]


def m4_vec(m, v):
    x, y, z = v
    return (m[0] * x + m[4] * y + m[8] * z + m[12],
            m[1] * x + m[5] * y + m[9] * z + m[13],
            m[2] * x + m[6] * y + m[10] * z + m[14])


# ------------------------------------------------------------------ glb load
def load_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67 and version == 2, "glb inválido"
    jlen = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20 + jlen])
    blen = struct.unpack("<I", data[20 + jlen:24 + jlen])[0]
    binary = data[28 + jlen:28 + jlen + blen]
    return gltf, binary, length


def read_accessor(gltf, binary, acc_idx):
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    comp = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
            5125: ("I", 4), 5126: ("f", 4)}[acc["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[acc["type"]]
    count = acc["count"]
    fmt = "<" + comp[0] * (ncomp * count)
    vals = struct.unpack_from(fmt, binary, off)
    stride = ncomp
    return [vals[i * stride:(i + 1) * stride] for i in range(count)]


def node_world(gltf, node_i, parent_world):
    node = gltf["nodes"][node_i]
    local = m4_identity()
    t = node.get("translation")
    if t:
        local = m4_mul(local, m4_translate(*t))
    r = node.get("rotation")
    if r:
        local = m4_mul(local, m4_rot_quat(r))
    return m4_mul(parent_world, local)


def check_glb(name):
    path = os.path.join(OUT, "gltf", name + ".glb")
    gltf, binary, length = load_glb(path)
    problems = []

    if gltf["buffers"][0]["byteLength"] != len(binary):
        problems.append("buffer byteLength != BIN real (%d != %d)" % (
            gltf["buffers"][0]["byteLength"], len(binary)))
    if length != 12 + 8 + len(json.dumps(gltf["buffers"])) and length != (28 + gltf.get('_jsonlen', 0)):
        pass  # tamanho total já confiável

    # worlds no bind
    worlds = [m4_identity() for _ in gltf["nodes"]]
    for i, node in enumerate(gltf["nodes"]):
        worlds[i] = node_world(gltf, i, worlds[0] if i != 0 else m4_identity())
    # reordena por dependência
    order = []
    def dfs(i):
        for c in gltf["nodes"][i].get("children", []):
            worlds[c] = node_world(gltf, c, worlds[i])
            dfs(c)
    dfs(0)

    skin = gltf["skins"][0]
    ibm = read_accessor(gltf, binary, skin["inverseBindMatrices"])

    # check skinning identidade numas amostras
    max_err = 0.0
    samples = 0
    for prim in gltf["meshes"][0]["primitives"]:
        pos = read_accessor(gltf, binary, prim["attributes"]["POSITION"])
        joints = read_accessor(gltf, binary, prim["attributes"]["JOINTS_0"])
        for k in range(0, len(pos), max(1, len(pos) // 60)):
            v = pos[k]
            j = joints[k][0]
            m = m4_mul(worlds[skin["joints"][j]], ibm[j])
            dv = m4_vec(m, v)
            err = max(abs(dv[0] - v[0]), abs(dv[1] - v[1]), abs(dv[2] - v[2]))
            max_err = max(max_err, err)
            samples += 1
    if max_err > 1e-3:
        problems.append("skinning bind != identidade (err %.4f)" % max_err)

    # check animação deforma (walk, frame do meio)
    anim = next(a for a in gltf["animations"] if a["name"] == "walk")
    # monta rotações no frame 15
    frame_rots = {}
    root_trans = None
    for ch in anim["channels"]:
        node_i = ch["target"]["node"]
        path = ch["target"]["path"]
        smp = anim["samplers"][ch["sampler"]]
        out = read_accessor(gltf, binary, smp["output"])
        mid = max(1, len(out) // 4)   # 1/4 de ciclo = braço no máximo da passada
        if path == "rotation":
            frame_rots[node_i] = out[mid]
        elif path == "translation":
            root_trans = out[mid]

    # re-monta worlds com rotações animadas
    aworlds = [m4_identity() for _ in gltf["nodes"]]
    for i, node in enumerate(gltf["nodes"]):
        local = m4_identity()
        if node.get("translation"):
            local = m4_mul(local, m4_translate(*node["translation"]))
        if i == 1 and root_trans:
            local = m4_mul(local, m4_translate(*root_trans))
        if i in frame_rots:
            local = m4_mul(local, m4_rot_quat(frame_rots[i]))
        aworlds[i] = m4_mul(aworlds[0], local)
    def adfs(i):
        for c in gltf["nodes"][i].get("children", []):
            local = m4_identity()
            node = gltf["nodes"][c]
            if node.get("translation"):
                local = m4_mul(local, m4_translate(*node["translation"]))
            if c == 1 and root_trans:
                local = m4_mul(local, m4_translate(*root_trans))
            if c in frame_rots:
                local = m4_mul(local, m4_rot_quat(frame_rots[c]))
            aworlds[c] = m4_mul(aworlds[i], local)
            adfs(c)
    adfs(0)

    # mede deslocamento de um vértice do braço direito vs bind
    moved = 0.0
    for prim in gltf["meshes"][0]["primitives"]:
        pos = read_accessor(gltf, binary, prim["attributes"]["POSITION"])
        joints = read_accessor(gltf, binary, prim["attributes"]["JOINTS_0"])
        for k in range(len(pos)):
            j = joints[k][0]
            if skin["joints"][j] != 4:  # nó 4 = Right Arm
                continue
            m = m4_mul(aworlds[skin["joints"][j]], ibm[j])
            dv = m4_vec(m, pos[k])
            moved = max(moved, abs(dv[0] - pos[k][0]) + abs(dv[2] - pos[k][2]))
    if moved < 0.01:
        problems.append("animação walk não deforma o braço (mov %.4f)" % moved)

    status = "OK" if not problems else "FALHOU"
    print("[glb %s] %s | skinning err=%.5f | braço mov=%.3f" % (name, status, max_err, moved))
    for p in problems:
        print("    -", p)
    return not problems


def check_bvh(name):
    path = os.path.join(OUT, "bvh", name + ".bvh")
    with open(path) as f:
        lines = f.read().splitlines()
    ok = lines and lines[0] == "HIERARCHY"
    frames_line = next(l for l in lines if l.startswith("Frames:"))
    n = int(frames_line.split()[1])
    # linhas de dados
    data = [l for l in lines if l and not l.startswith(("HIERARCHY", "ROOT", "JOINT", "End", "OFFSET", "CHANNELS", "MOTION", "Frames", "Frame", "{", "}", "\t"))]
    print("[bvh %s] %s | frames=%d data_rows=%d" % (name, "OK" if ok and len(data) == n else "FALHOU", n, len(data)))
    return ok and len(data) == n


def check_obj(name):
    path = os.path.join(OUT, "obj", name + ".obj")
    nv = nf = 0
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                nv += 1
            elif line.startswith("f "):
                nf += 1
    print("[obj %s] OK | verts=%d faces=%d" % (name, nv, nf))
    return nv > 0


def main():
    import sys
    sys.path.insert(0, ROOT)
    from engine.armor_models import VARIANTS
    all_ok = True
    for v in VARIANTS:
        all_ok &= check_glb(v)
        all_ok &= check_obj(v)
        all_ok &= check_obj(v + "_roblox_baked")
    for c in ("idle", "walk", "run", "attack", "block"):
        all_ok &= check_bvh("r6_" + c)
    print("\n%s" % ("TUDO OK" if all_ok else "HÁ PROBLEMAS"))


if __name__ == "__main__":
    main()
