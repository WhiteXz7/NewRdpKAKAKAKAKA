"""mesh.py — Malha poligonal + primitivas paramétricas + exportação OBJ/MTL.

Este é o "motor de modelagem" próprio (substituto do Blender para esta tarefa):
gera geometria procedimental fechada/watertight onde faz sentido, pronta para
ser importada no Roblox Studio, Blender, Cascadeur etc.
"""

import math
from . import math3d as m3

# Ordem de vértices de um cubo: vértices numerados por bit (x, y, z) = bit0, bit1, bit2.
_BOX_CORNERS = [
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
]
# Faces (quads, CCW visto de fora) indexadas sobre os vértices do cubo acima.
_BOX_QUADS = [
    (4, 5, 6, 7),  # +Z frente
    (1, 0, 3, 2),  # -Z atras
    (0, 4, 7, 3),  # -X esquerda
    (5, 1, 2, 6),  # +X direita
    (3, 7, 6, 2),  # +Y topo
    (0, 1, 5, 4),  # -Y fundo
]


class Mesh:
    __slots__ = ("name", "verts", "faces", "material")

    def __init__(self, name="mesh", material="steel"):
        self.name = name
        self.verts = []      # lista de (x, y, z)
        self.faces = []      # lista de tuplas de indices (3 ou 4+)
        self.material = material

    def add_vert(self, p):
        self.verts.append(tuple(float(c) for c in p))
        return len(self.verts) - 1

    def add_face(self, idxs):
        self.faces.append(tuple(idxs))

    def transform(self, fn):
        """Aplica fn(v)->v a todos os vértices."""
        self.verts = [fn(v) for v in self.verts]
        return self

    def translate(self, t):
        return self.transform(lambda v: m3.vadd(v, t))

    def rotate_x(self, a, pivot=(0, 0, 0)):
        m = m3.mat_rot_x(a)
        return self.transform(lambda v: m3.rot_about(pivot, m, v))

    def rotate_y(self, a, pivot=(0, 0, 0)):
        m = m3.mat_rot_y(a)
        return self.transform(lambda v: m3.rot_about(pivot, m, v))

    def rotate_z(self, a, pivot=(0, 0, 0)):
        m = m3.mat_rot_z(a)
        return self.transform(lambda v: m3.rot_about(pivot, m, v))

    def scale(self, s):
        return self.transform(lambda v: (v[0] * s[0], v[1] * s[1], v[2] * s[2]))

    def mirror_x(self):
        return self.transform(lambda v: (-v[0], v[1], v[2]))

    def mirror_z(self):
        return self.transform(lambda v: (v[0], v[1], -v[2]))

    def flipped_faces(self):
        """Inverte o winding (para espelhar mantendo faces orientadas corretamente)."""
        for i, f in enumerate(self.faces):
            self.faces[i] = tuple(reversed(f))
        return self

    def merge(self, other):
        base = len(self.verts)
        self.verts.extend(other.verts)
        for f in other.faces:
            self.add_face(tuple(i + base for i in f))
        return self

    def copy(self):
        m = Mesh(self.name, self.material)
        m.verts = list(self.verts)
        m.faces = list(self.faces)
        return m

    def triangulate(self):
        tris = []
        for f in self.faces:
            for k in range(1, len(f) - 1):
                tris.append((f[0], f[k], f[k + 1]))
        self.faces = tris
        return self

    def n_faces(self):
        return len(self.faces)

    def n_tris(self):
        return sum(len(f) - 2 for f in self.faces)


# ------------------------------------------------------------------------------
# Primitivas
# ------------------------------------------------------------------------------

def box(x0, x1, y0, y1, z0, z1, name="box", material="steel"):
    """Caixa fechada axis-aligned."""
    m = Mesh(name, material)
    for c in _BOX_CORNERS:
        m.add_vert((x0 + c[0] * (x1 - x0), y0 + c[1] * (y1 - y0), z0 + c[2] * (z1 - z0)))
    for f in _BOX_QUADS:
        m.add_face(f)
    return m


def tapered_box(x0b, x1b, x0t, x1t, y0, y1, z0b, z1b, z0t, z1t, name="tbox", material="steel"):
    """Prisma fechado com base e topo de larguras diferentes (trapezoidal)."""
    m = Mesh(name, material)
    m.add_vert((x0b, y0, z0b)); m.add_vert((x1b, y0, z0b))
    m.add_vert((x1b, y0, z1b)); m.add_vert((x0b, y0, z1b))
    m.add_vert((x0t, y1, z0t)); m.add_vert((x1t, y1, z0t))
    m.add_vert((x1t, y1, z1t)); m.add_vert((x0t, y1, z1t))
    # frente (+z) e atras (-z) -> dois quads verticais
    m.add_face((0, 1, 5, 4))
    m.add_face((2, 3, 7, 6))
    m.add_face((0, 4, 7, 3))
    m.add_face((1, 2, 6, 5))
    m.add_face((4, 5, 6, 7))   # topo
    m.add_face((0, 3, 2, 1))   # fundo
    return m


def tube(r0, r1, y0, y1, segments=24, a0=0.0, a1=2 * math.pi, name="tube",
         material="steel", cap_bottom=False, cap_top=False):
    """Casca de cilindro/frustum (sem tampas por padrão). a0..a1 define o arco (rad, plano XZ)."""
    # garante que o anel 0 seja o mais baixo (winding consistente)
    if y0 > y1:
        r0, r1, y0, y1 = r1, r0, y1, y0
    m = Mesh(name, material)
    segs = max(3, segments)
    ring0 = []
    ring1 = []
    for i in range(segs + 1):
        t = a0 + (a1 - a0) * i / segs
        c, s = math.cos(t), math.sin(t)
        ring0.append(m.add_vert((r0 * c, y0, r0 * s)))
        ring1.append(m.add_vert((r1 * c, y1, r1 * s)))
    for i in range(segs):
        m.add_face((ring0[i], ring1[i], ring1[i + 1], ring0[i + 1]))
    # tampas (em leque)
    if cap_bottom:
        c = m.add_vert((0.0, y0, 0.0))
        for i in range(segs):
            m.add_face((c, ring0[i], ring0[i + 1]))
    if cap_top:
        c = m.add_vert((0.0, y1, 0.0))
        for i in range(segs):
            m.add_face((c, ring1[i + 1], ring1[i]))
    return m


def lathe(profile, segments=32, a0=0.0, a1=2 * math.pi, name="lathe", material="steel"):
    """Superficie de revolução em torno de Y. profile = lista de (raio, y) do topo à base."""
    m = Mesh(name, material)
    segs = max(3, segments)
    ring_idx = []
    for p in profile:
        r, y = p
        idxs = []
        for i in range(segs + 1):
            t = a0 + (a1 - a0) * i / segs
            idxs.append(m.add_vert((r * math.cos(t), y, r * math.sin(t))))
        ring_idx.append(idxs)
    for r in range(len(profile) - 1):
        for i in range(segs):
            a = ring_idx[r][i]; b = ring_idx[r][i + 1]
            d = ring_idx[r + 1][i + 1]; c = ring_idx[r + 1][i]
            m.add_face((a, c, d, b))
    return m


def thicken_surface(grid, thickness=0.1, normal_flip=False, name="plate", material="steel"):
    """Transforma uma grade de pontos (rows x cols) numa placa sólida com espessura.

    grid = lista de linhas (rows), cada linha = lista de pontos (x,y,z).
    A normal é estimada por diferenças centrais: n = cross(dP/dcol, dP/drow),
    que para uma superficie "de frente" (z crescendo) aponta para +z.
    A face frontal fica em `grid`; a face de trás é deslocada -n*thickness
    (ou seja, a espessura cresce para DENTRO, preservando o contorno externo).
    Use normal_flip=True quando a superficie externa aponta para o lado oposto
    (ex.: placa dorsal, cujo exterior é -z).
    """
    rows = len(grid)
    cols = len(grid[0])
    m = Mesh(name, material)
    idx = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            idx[r][c] = m.add_vert(grid[r][c])

    def tnorm(r, c):
        c0, c1 = max(0, c - 1), min(cols - 1, c + 1)
        u = m3.vsub(grid[r][c1], grid[r][c0])
        r0, r1 = max(0, r - 1), min(rows - 1, r + 1)
        v = m3.vsub(grid[r1][c], grid[r0][c])
        n = m3.vcross(u, v)
        l = m3.vlen(n)
        if l < 1e-12:
            n = (0.0, 0.0, 1.0)
        else:
            n = m3.vmul(n, 1.0 / l)
        return m3.vneg(n) if normal_flip else n

    back = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = tnorm(r, c)
            back[r][c] = m.add_vert(m3.vsub(grid[r][c], m3.vmul(n, thickness)))

    # face frontal (outward = +n)
    for r in range(rows - 1):
        for c in range(cols - 1):
            m.add_face((idx[r][c], idx[r][c + 1], idx[r + 1][c + 1], idx[r + 1][c]))
    # face traseira (winding invertido)
    for r in range(rows - 1):
        for c in range(cols - 1):
            m.add_face((back[r][c], back[r + 1][c], back[r + 1][c + 1], back[r][c + 1]))
    # bordas (rim)
    for r in range(rows - 1):
        m.add_face((idx[r][0], idx[r + 1][0], back[r + 1][0], back[r][0]))
        m.add_face((idx[r][cols - 1], back[r][cols - 1], back[r + 1][cols - 1], idx[r + 1][cols - 1]))
    for c in range(cols - 1):
        m.add_face((idx[0][c], back[0][c], back[0][c + 1], idx[0][c + 1]))
        m.add_face((idx[rows - 1][c], idx[rows - 1][c + 1], back[rows - 1][c + 1], back[rows - 1][c]))
    return m


def fix_orientation(m, reference=None):
    """Garante que todas as faces apontem para 'fora' em relação ao centróide.

    Para cada face, calcula a normal; se apontar para o interior (centróide),
    inverte o winding. Seguro para cascas convexas/finas.
    """
    if not m.verts:
        return m
    c = reference
    if c is None:
        c = m3.vdiv(
            (sum(v[0] for v in m.verts), sum(v[1] for v in m.verts), sum(v[2] for v in m.verts)),
            len(m.verts))
    new = []
    for f in m.faces:
        if len(f) < 3:
            new.append(f)
            continue
        p0, p1, p2 = m.verts[f[0]], m.verts[f[1]], m.verts[f[2]]
        n = m3.vcross(m3.vsub(p1, p0), m3.vsub(p2, p0))
        mid = m3.vdiv(m3.vadd(m3.vadd(p0, p1), p2), 3.0)
        if m3.vdot(n, m3.vsub(mid, c)) < 0:
            new.append(tuple(reversed(f)))
        else:
            new.append(f)
    m.faces = new
    return m


def rounded_rect_grid(w, h, corner=0.08, segments=3):
    """Grade plana (no plano XY) de um retângulo com cantos arredondados.

    Retorna lista de linhas de pontos (x, y, 0). Usa a SDF de "rounded box".
    """
    hw, hh = w / 2.0, h / 2.0
    r = min(corner, hw, hh)
    bx, by = hw - r, hh - r
    if bx <= 0 or by <= 0:
        bx, by = hw, hh
        r = 0.0

    def sdf(px, py):
        qx = abs(px) - bx
        qy = abs(py) - by
        return math.hypot(max(qx, 0.0), max(qy, 0.0)) - r

    steps = segments * 4 + 1
    grid = []
    for j in range(steps):
        ty = -1.0 + 2.0 * j / (steps - 1)
        row = []
        for i in range(steps):
            tx = -1.0 + 2.0 * i / (steps - 1)
            px, py = tx * hw, ty * hh
            d = sdf(px, py)
            if d > 0:
                qx = abs(px) - bx
                qy = abs(py) - by
                if qx <= 0:
                    py = math.copysign(by + r, py)
                elif qy <= 0:
                    px = math.copysign(bx + r, px)
                else:
                    g = (max(qx, 0.0), max(qy, 0.0))
                    gl = math.hypot(g[0], g[1]) or 1.0
                    px = math.copysign(bx + g[0] / gl * r, px)
                    py = math.copysign(by + g[1] / gl * r, py)
            row.append((px, py, 0.0))
        grid.append(row)
    return grid


def rounded_rect_plate(w, h, thickness, corner=0.08, segments=3, bulge=0.0,
                       name="plate", material="steel"):
    """Placa retangular com cantos arredondados, espessura em Z e leve abaulamento (bulge)."""
    grid = rounded_rect_grid(w, h, corner, segments)
    if bulge > 0:
        hw, hh = w / 2.0, h / 2.0
        for row in grid:
            for k, (px, py, _) in enumerate(row):
                ax = abs(px / hw); ay = abs(py / hh)
                lat = max(0.0, 1.0 - max(ax, ay) ** 2)
                row[k] = (px, py, bulge * lat)
    m = thicken_surface(grid, thickness, name=name, material=material)
    m.translate((0, 0, -thickness / 2.0))
    return m


def dome(radius, height, y0, segments=32, name="dome", material="steel"):
    """Meia-esfera / calota apontando para cima, apoiada em y0 (casca aberta na base).

    O ápice usa um raio mínimo (não 0) para evitar vértices degenerados.
    """
    prof = []
    steps = 12
    for i in range(steps + 1):
        t = i / steps                      # 0 = base, 1 = topo
        ang = t * math.pi / 2
        r = radius * math.cos(ang)
        if i == steps:
            r = radius * 0.008
        y = y0 + height * math.sin(ang)
        prof.append((r, y))
    return lathe(prof, segments=segments, name=name, material=material)


# ------------------------------------------------------------------------------
# Exportação OBJ / MTL
# ------------------------------------------------------------------------------

def compute_normals(m):
    """Normais por vértice (média das faces)."""
    acc = [(0.0, 0.0, 0.0) for _ in m.verts]
    for f in m.faces:
        if len(f) < 3:
            continue
        p0, p1, p2 = m.verts[f[0]], m.verts[f[1]], m.verts[f[2]]
        n = m3.vcross(m3.vsub(p1, p0), m3.vsub(p2, p0))
        nl = m3.vlen(n)
        if nl > 1e-12:
            n = m3.vmul(n, 1.0 / nl)
        for i in f:
            acc[i] = m3.vadd(acc[i], n)
    return [m3.vnorm(a) for a in acc]


def write_obj(path, meshes, mtl_name="armor.mtl", up_axis="y"):
    """Escreve um .obj com vários objetos (grupos 'o'). Usa 1 arquivo MTL."""
    with open(path, "w") as f:
        f.write("# Armadura R6 - motor de modelagem proprio (Python)\n")
        f.write("mtllib %s\n" % mtl_name)
        vbase = 0
        for m in meshes:
            f.write("o %s\n" % m.name)
            for v in m.verts:
                f.write("v %.6f %.6f %.6f\n" % v)
            normals = compute_normals(m)
            for n in normals:
                f.write("vn %.6f %.6f %.6f\n" % n)
            f.write("usemtl %s\n" % m.material)
            for face in m.faces:
                # OBJ: indice base 1; vertice/normal iguais (normal suavizada por vertice)
                idxs = [str(i + 1 + vbase) for i in face]
                f.write("f " + " ".join(idxs) + "\n")
            vbase += len(m.verts)


MTL_PALETTE = {
    # materiais da armadura (nome -> (Kd rgb, Ks, Ns, metallic-ish via Ks alto))
    "steel":        ((0.46, 0.48, 0.52), (0.8, 0.82, 0.86), 128.0),
    "steel_dark":   ((0.28, 0.30, 0.33), (0.55, 0.58, 0.62), 96.0),
    "steel_light":  ((0.60, 0.62, 0.66), (0.9, 0.9, 0.95), 160.0),
    "brass":        ((0.72, 0.58, 0.30), (0.85, 0.72, 0.45), 140.0),
    "leather":      ((0.36, 0.23, 0.14), (0.12, 0.10, 0.08), 12.0),
    "mail":         ((0.33, 0.35, 0.38), (0.4, 0.42, 0.46), 60.0),
    "lacquer_red":  ((0.55, 0.09, 0.08), (0.5, 0.4, 0.35), 64.0),
    "lacquer_black":((0.10, 0.10, 0.11), (0.5, 0.5, 0.55), 96.0),
    "lacquer_gold": ((0.70, 0.55, 0.20), (0.8, 0.72, 0.4), 128.0),
    "silk":         ((0.16, 0.22, 0.46), (0.1, 0.1, 0.12), 8.0),
    "fabric":       ((0.24, 0.30, 0.50), (0.06, 0.06, 0.08), 6.0),
    "rivet":        ((0.62, 0.52, 0.34), (0.7, 0.6, 0.45), 90.0),
}


def write_mtl(path, palette=None):
    pal = palette or MTL_PALETTE
    with open(path, "w") as f:
        f.write("# Materiais da armadura (gerado)\n")
        for name, (kd, ks, ns) in pal.items():
            f.write("newmtl %s\n" % name)
            f.write("Kd %.4f %.4f %.4f\n" % kd)
            f.write("Ks %.4f %.4f %.4f\n" % ks)
            f.write("Ns %.1f\n" % ns)
            f.write("Ka 0.02 0.02 0.02\n")
            f.write("illum 2\n\n")
