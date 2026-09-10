"""rig.py — Esqueleto do rig R6 + skinning (substituto do rigging do Blender).

O R6 tem 6 "peças" articuladas, cada uma girando em torno de 1 junta (Motor6D).
Esqueleto usado (nomes = junta do Roblox):

    HumanoidRootPart (0,1,0)
      ├─ Torso          (junta "Root Hip")      pivô (0,1,0)
      │    ├─ Head      (junta "Neck")          pivô (0,3,0)
      │    ├─ Right Arm (junta "Right Shoulder") pivô (1.5,3,0)
      │    ├─ Left Arm  (junta "Left Shoulder")  pivô (-1.5,3,0)
      │    ├─ Right Leg (junta "Right Hip")      pivô (0.5,2,0)
      │    └─ Left Leg  (junta "Left Hip")       pivô (-0.5,2,0)
"""

import math
from . import math3d as m3


class Joint:
    __slots__ = ("name", "parent", "offset", "world_rest", "r6_motor")

    def __init__(self, name, parent, offset, r6_motor=None):
        self.name = name
        self.parent = parent            # índice do pai (ou -1)
        self.offset = tuple(offset)     # translação local (espaço do pai)
        self.world_rest = (0.0, 0.0, 0.0)
        self.r6_motor = r6_motor        # nome do Motor6D correspondente no Roblox


R6_MOTORS = {
    "Torso": "Root Hip",
    "Head": "Neck",
    "Right Arm": "Right Shoulder",
    "Left Arm": "Left Shoulder",
    "Right Leg": "Right Hip",
    "Left Leg": "Left Hip",
}

# Centro de cada PARTE do R6 (onde o MeshPart fica no Studio). É em torno
# desses centros que a armadura foi modelada; ao soldar com C0=C1=identidade,
# cada peça fica perfeitamente alinhada à sua parte.
R6_PART_CENTERS = {
    "Torso": (0.0, 2.0, 0.0),
    "Head": (0.0, 3.6, 0.0),
    "Right Arm": (1.5, 2.0, 0.0),
    "Left Arm": (-1.5, 2.0, 0.0),
    "Right Leg": (0.5, 1.0, 0.0),
    "Left Leg": (-0.5, 1.0, 0.0),
}


class Skeleton:
    def __init__(self):
        self.joints = []   # ordem: pai sempre antes dos filhos

    def add(self, name, parent=-1, offset=(0, 0, 0), r6_motor=None):
        self.joints.append(Joint(name, parent, offset, r6_motor))
        return len(self.joints) - 1

    def by_name(self, name):
        for i, j in enumerate(self.joints):
            if j.name == name:
                return i
        return -1

    def build_rest(self):
        """Calcula posições globais de descanso (bind)."""
        for i, j in enumerate(self.joints):
            if j.parent < 0:
                j.world_rest = j.offset
            else:
                j.world_rest = m3.vadd(self.joints[j.parent].world_rest, j.offset)
        return self

    def forward(self, local_rots):
        """Calcula matrizes globais de cada junta dadas rotações locais (dict nome->(rx,ry,rz)).

        Retorna lista de matrizes globais 3x3 (só rotação; a translação é o pivô).
        local_rots usa ângulos de Euler internos (R = Rz·Ry·Rx, X aplicado primeiro).
        """
        globals_ = [m3.mat_ident() for _ in self.joints]
        for i, j in enumerate(self.joints):
            local = m3.mat_ident()
            if j.name in local_rots and j.parent >= 0:
                rx, ry, rz = local_rots[j.name]
                local = m3.euler_xyz(rx, ry, rz)
            if j.parent < 0:
                globals_[i] = local
            else:
                globals_[i] = m3.mat_mul(globals_[j.parent], local)
        return globals_

    def deform(self, verts, bone_index, globals_):
        """Aplica a transformação de uma junta a uma lista de vértices (skinning rígida).

        bone_index = índice da junta à qual os vértices pertencem.
        """
        pivot = self.joints[bone_index].world_rest
        g = globals_[bone_index]
        out = []
        for v in verts:
            d = m3.vsub(v, pivot)
            out.append(m3.vadd(pivot, m3.mat_vec(g, d)))
        return out

    def inverse_bind(self):
        """Matrizes inverse-bind 4x4 (para glTF). Só translação no descanso."""
        ib = []
        for j in self.joints:
            p = j.world_rest
            # matriz coluna-major 4x4 (OpenGL/glTF)
            m = [1, 0, 0, 0,
                 0, 1, 0, 0,
                 0, 0, 1, 0,
                 -p[0], -p[1], -p[2], 1]
            ib.append(m)
        return ib


def build_r6_skeleton():
    sk = Skeleton()
    sk.add("HumanoidRootPart", -1, (0.0, 1.0, 0.0))
    sk.add("Torso", 0, (0.0, 0.0, 0.0), R6_MOTORS["Torso"])
    sk.add("Head", 1, (0.0, 2.0, 0.0), R6_MOTORS["Head"])
    sk.add("Right Arm", 1, (1.5, 2.0, 0.0), R6_MOTORS["Right Arm"])
    sk.add("Left Arm", 1, (-1.5, 2.0, 0.0), R6_MOTORS["Left Arm"])
    sk.add("Right Leg", 1, (0.5, 1.0, 0.0), R6_MOTORS["Right Leg"])
    sk.add("Left Leg", 1, (-0.5, 1.0, 0.0), R6_MOTORS["Left Leg"])
    sk.build_rest()
    return sk


def deform_mesh(mesh, skeleton, bone_name, globals_):
    """Retorna uma cópia da malha com os vértices transformados pelo osso dado."""
    idx = skeleton.by_name(bone_name)
    if idx < 0:
        return mesh.copy()
    out = mesh.copy()
    out.verts = skeleton.deform(mesh.verts, idx, globals_)
    return out


def pose_parts(parts, pose, root_pos=None):
    """Aplica uma pose (dict nome->(rx,ry,rz)) às peças (Mesh, osso).

    root_pos = posição (x,y,z) da raiz; se dado, desloca tudo por (root_pos - (0,1,0))
    (o "bob" vertical do centro de massa).
    """
    sk = build_r6_skeleton()
    globals_ = sk.forward(pose)
    delta = (0.0, 0.0, 0.0)
    if root_pos is not None:
        delta = (root_pos[0] - 0.0, root_pos[1] - 1.0, root_pos[2] - 0.0)
    out = []
    for mesh, bone in parts:
        m = deform_mesh(mesh, sk, bone, globals_)
        if delta != (0.0, 0.0, 0.0):
            m.translate(delta)
        out.append((m, bone))
    return out
