"""gltf.py — Exportador glTF 2.0 binário (.glb) com esqueleto R6, skinning e animações.

Um único .glb por variante contém:
  * esqueleto R6 (HumanoidRootPart + 6 partes, hierarquia igual ao Roblox),
  * malha da armadura skinada (cada peça segue seu osso),
  * animações de Idle / Walk / Run (rotações locais + deslocamento vertical da raiz).

Convenção: +Y para cima, +Z para frente — igual ao glTF nativo, sem troca de eixos.
"""

import json
import struct
import math

from . import math3d as m3
from .animation import local_quats
from .rig import build_r6_skeleton
from .mesh import MTL_PALETTE

_GLTF_MATERIAL = {
    "steel":        (0.95, 0.35),
    "steel_dark":   (0.95, 0.35),
    "steel_light":  (0.95, 0.30),
    "brass":        (0.90, 0.40),
    "rivet":        (0.90, 0.40),
    "mail":         (0.80, 0.60),
    "leather":      (0.00, 0.90),
    "lacquer_red":  (0.20, 0.35),
    "lacquer_black":(0.20, 0.35),
    "lacquer_gold": (0.30, 0.30),
    "silk":         (0.00, 0.85),
    "fabric":       (0.00, 0.85),
}


class _Bin:
    def __init__(self):
        self.data = bytearray()

    def pad4(self):
        while len(self.data) % 4:
            self.data.append(0)

    def add(self, b):
        off = len(self.data)
        self.data.extend(b)
        return off


def _f32s(vals):
    return struct.pack("<%df" % len(vals), *vals)


def _u16s(vals):
    return struct.pack("<%dH" % len(vals), *vals)


def _u32s(vals):
    return struct.pack("<%dI" % len(vals), *vals)


def build_glb(parts, clips, fps, variant_name):
    """parts = lista de (Mesh, osso). clips = dict nome -> lista de (root_pos, pose)."""
    skeleton = build_r6_skeleton()
    name_to_node = {
        "HumanoidRootPart": 1, "Torso": 2, "Head": 3,
        "Right Arm": 4, "Left Arm": 5, "Right Leg": 6, "Left Leg": 7,
    }
    node_to_joint = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5}  # node -> índice em skin.joints

    nodes = [
        {"name": "Armature", "children": [1, 8]},
        {"name": "HumanoidRootPart", "translation": [0.0, 1.0, 0.0], "children": [2]},
        {"name": "Torso", "translation": [0.0, 0.0, 0.0], "children": [3, 4, 5, 6, 7]},
        {"name": "Head", "translation": [0.0, 2.0, 0.0]},
        {"name": "Right Arm", "translation": [1.5, 2.0, 0.0]},
        {"name": "Left Arm", "translation": [-1.5, 2.0, 0.0]},
        {"name": "Right Leg", "translation": [0.5, 1.0, 0.0]},
        {"name": "Left Leg", "translation": [-0.5, 1.0, 0.0]},
    ]
    # nó 8 = malha da armadura (filho da Armature, transform identidade -> vértices em espaço-mundo)
    nodes.append({"name": "Armor", "mesh": 0, "skin": 0})

    bin_ = _Bin()
    buffer_views = []
    accessors = []
    materials = []
    mesh_primitives = []

    def push_view(data, target=None):
        bin_.pad4()
        off = bin_.add(data)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    def push_accessor(view_idx, comp_type, count, acc_type, mins=None, maxs=None):
        acc = {"bufferView": view_idx, "componentType": comp_type, "count": count, "type": acc_type}
        if mins is not None:
            acc["min"] = mins
            acc["max"] = maxs
        accessors.append(acc)
        return len(accessors) - 1

    # materiais
    mat_names = sorted(set(m.material for m, _ in parts))
    mat_index = {}
    for mn in mat_names:
        mat_index[mn] = len(materials)
        kd = MTL_PALETTE.get(mn, MTL_PALETTE["steel"])[0]
        met, rough = _GLTF_MATERIAL.get(mn, (0.9, 0.4))
        materials.append({
            "pbrMetallicRoughness": {
                "baseColorFactor": [kd[0], kd[1], kd[2], 1.0],
                "metallicFactor": met, "roughnessFactor": rough,
            },
            "name": mn,
        })

    # primitivas (uma por peça)
    from .mesh import compute_normals
    for (mesh, bone) in parts:
        mesh.triangulate()
        verts = mesh.verts
        normals = compute_normals(mesh)
        idxs = []
        for f in mesh.faces:
            idxs.extend(f)
        joint = node_to_joint[name_to_node[bone]]  # índice no array skin.joints

        pos_data = b"".join(struct.pack("<3f", *v) for v in verts)
        nor_data = b"".join(struct.pack("<3f", *n) for n in normals)
        idx_data = _u16s(idxs) if len(verts) <= 65535 else _u32s(idxs)
        jnt_data = _u16s([joint, joint, joint, joint] * len(verts))
        wgt_data = _f32s([1.0, 0.0, 0.0, 0.0] * len(verts))

        prim = {"attributes": {}, "material": mat_index[mesh.material]}
        pv = push_view(pos_data, 34962)
        prim["attributes"]["POSITION"] = push_accessor(pv, 5126, len(verts), "VEC3")
        nv = push_view(nor_data, 34962)
        prim["attributes"]["NORMAL"] = push_accessor(nv, 5126, len(verts), "VEC3")
        jv = push_view(jnt_data, 34962)
        prim["attributes"]["JOINTS_0"] = push_accessor(jv, 5123, len(verts), "VEC4")
        wv = push_view(wgt_data, 34962)
        prim["attributes"]["WEIGHTS_0"] = push_accessor(wv, 5126, len(verts), "VEC4")
        iv = push_view(idx_data, 34963)
        prim["indices"] = push_accessor(iv, 5123 if len(verts) <= 65535 else 5125, len(idxs), "SCALAR")
        mesh_primitives.append(prim)

    # inverseBindMatrices (os 6 ossos, ordem: Torso, Head, RA, LA, RL, LL)
    ibm = []
    for j in skeleton.joints[1:]:
        x, y, z = j.world_rest
        # coluna-major 4x4 (glTF)
        ibm += [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1]
    ibm_data = _f32s(ibm)
    ibm_view = push_view(ibm_data)
    ibm_acc = push_accessor(ibm_view, 5126, 6, "MAT4")

    # animações
    animations = []
    for clip_name, clip in clips.items():
        times = [i / fps for i in range(len(clip))]
        time_data = _f32s(times)
        time_view = push_view(time_data)
        time_acc = push_accessor(time_view, 5126, len(times), "SCALAR",
                                 mins=[min(times)], maxs=[max(times)])

        channels = []
        samplers = []

        # translação da raiz (bob)
        root_pos = [_f32s([p[0], p[1], p[2]]) for (p, _) in clip]
        root_data = b"".join(root_pos)
        root_view = push_view(root_data)
        root_acc = push_accessor(root_view, 5126, len(clip), "VEC3")
        samplers.append({"input": time_acc, "output": root_acc,
                         "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1,
                         "target": {"node": 1, "path": "translation"}})

        # rotações dos 6 ossos
        for j in skeleton.joints[1:]:
            quats = []
            for (root_pos, pose) in clip:
                q = local_quats(skeleton, pose)[j.name]
                quats.append(_f32s(q))
            qdata = b"".join(quats)
            qview = push_view(qdata)
            qacc = push_accessor(qview, 5126, len(clip), "VEC4")
            samplers.append({"input": time_acc, "output": qacc,
                             "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1,
                             "target": {"node": name_to_node[j.name], "path": "rotation"}})

        animations.append({"name": clip_name, "samplers": samplers, "channels": channels})

    skin = {
        "joints": [2, 3, 4, 5, 6, 7],
        "skeleton": 2,
        "inverseBindMatrices": ibm_acc,
    }

    gltf = {
        "asset": {"version": "2.0", "generator": "armor_r6-python-engine"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": nodes,
        "meshes": [{"name": "Armor_" + variant_name, "primitives": mesh_primitives}],
        "skins": [skin],
        "materials": materials,
        "animations": animations,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_.data)}],
    }

    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(bin_.data)
    out = bytearray()
    out += struct.pack("<I", 0x46546C67)          # 'glTF'
    out += struct.pack("<II", 2, total)
    out += struct.pack("<I", len(js))
    out += struct.pack("<I", 0x4E4F534A)          # 'JSON'
    out += js
    out += struct.pack("<I", len(bin_.data))
    out += struct.pack("<I", 0x004E4942)          # 'BIN\0'
    out += bin_.data
    return bytes(out)
