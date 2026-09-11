"""armor_models.py — Modelagem procedural das armaduras históricas.

Convenções (rig R6, Y para cima, +Z frente, +X direita do personagem):
  * Torso:  x∈[-1,1],  y∈[1,3],  z∈[-0.5,0.5]
  * Cabeça: esfera r≈0.62, centro (0, 3.6, 0)
  * Braço Direito:  x∈[1,2], y∈[1,3]   (centro x=1.5)
  * Braço Esquerdo: x∈[-2,-1]
  * Perna Direita:  x∈[0,1], y∈[0,2]   (centro x=0.5)
  * Perna Esquerda: x∈[-1,0]

Cada função de peça devolve uma lista de Mesh (pode ser espelhada para o lado esquerdo).
A função build_variant() monta o conjunto completo e associa cada peça a um "osso"
(parte do R6) para skinning/solda no Roblox.
"""

import math
from . import math3d as m3
from .mesh import (Mesh, box, tube, lathe, dome, thicken_surface,
                   rounded_rect_plate, box_tube, fix_orientation)

ARM_R = 1.5   # centro x do braço direito
LEG_R = 0.5   # centro x da perna direita

_FACING = {
    "+y": (0.0, 0.0),
    "-y": (math.pi, 0.0),
    "+z": (math.pi / 2, 0.0),
    "-z": (-math.pi / 2, 0.0),
    "+x": (0.0, -math.pi / 2),
    "-x": (0.0, math.pi / 2),
}


def _out(m):
    return fix_orientation(m)


def _mirror(m, name):
    n = m.copy()
    n.name = name
    n.mirror_x()
    n.flipped_faces()
    return n


def _orient(m, facing):
    rx, rz = _FACING[facing]
    if rx:
        m.rotate_x(rx)
    if rz:
        m.rotate_z(rz)
    return m


def _cup(radius, depth, center, facing, name="cup", material="steel"):
    """Calota aberta (copo) com a boca aberta apontando para 'facing'."""
    d = dome(radius, depth, 0.0, segments=20, name=name, material=material)
    _orient(d, facing)
    d.translate(center)
    return d


def _cone(r_base, height, center, facing, name="cone", material="steel", r_top=0.008):
    """Cone com base em 'center' e ápice apontando para 'facing'."""
    c = lathe([(r_base, 0.0), (r_top, height)], segments=16, name=name, material=material)
    _orient(c, facing)
    c.translate(center)
    return c


def _rivets(points, size=0.05, name="rivets", material="rivet"):
    """Pequenos pinos de rebite (caixas) nas posições dadas (x,y,z)."""
    m = Mesh(name, material)
    for (x, y, z) in points:
        b = box(x - size / 2, x + size / 2, y - size / 2, y + size / 2,
                z - size / 3, z + size / 3, material=material)
        m.merge(b)
    return m


# ==============================================================================
# Tronco
# ==============================================================================

def _chest_grid(front=True, bulge_amp=0.16, y_top=2.72, y_bottom=1.15):
    """Grade da placa peitoral/dorsal (curvada). front=False gera a dorsal."""
    sign = 1.0 if front else -1.0
    cols, rows = 25, 20
    grid = []
    for r in range(rows):
        h = r / (rows - 1)
        y = y_bottom + h * (y_top - y_bottom)
        row = []
        for c in range(cols):
            x = -1.0 + 2.0 * c / (cols - 1)
            ax = abs(x)
            lat = max(0.0, 1.0 - (ax / 1.03) ** 2)
            b = math.sin(math.pi * m3.clamp((h - 0.06) / 0.88, 0.0, 1.0))
            b = b * (0.5 + 0.5 * b)
            ridge = 0.0
            if front and h < 0.42:
                ridge = 0.035 * (1.0 - ax) * ((0.42 - h) / 0.42)
            z = sign * (0.52 + bulge_amp * b * lat) - (ridge if front else 0.0)
            row.append((x, y, z))
        grid.append(row)
    return grid


def cuirass_front():
    g = _chest_grid(front=True)
    m = thicken_surface(g, 0.06, name="cuirass_front", material="steel")
    return _out(m)


def cuirass_back():
    g = _chest_grid(front=False, bulge_amp=0.09, y_top=2.60)
    m = thicken_surface(g, 0.06, normal_flip=True, name="cuirass_back", material="steel")
    return _out(m)


def gorget():
    m = tube(0.72, 1.02, 2.85, 3.35, segments=24, name="gorget", material="steel")
    return _out(m)


def fauld(material="steel", n_front=3, n_back=2, back_material=None):
    """Fraldão: lâminas frontais (arco em volta de +z) e culet (arco em -z).

    O tronco do R6 é largo e raso (2x1), então o fraldão é elíptico:
    escala em Z para acompanhar a profundidade do corpo.
    """
    meshes = []
    for i in range(n_front):
        y_top = 2.02 - i * 0.20
        y_bot = y_top - 0.17
        r_top = 1.02 + i * 0.10
        r_bot = r_top + 0.10
        t = tube(r_top, r_bot, y_top, y_bot, segments=24,
                 a0=math.pi / 6, a1=5 * math.pi / 6, name="fauld_front_%d" % i, material=material)
        t.scale((1.0, 1.0, 0.72))
        meshes.append(_out(t))
    bm = back_material or material
    for i in range(n_back):
        y_top = 1.98 - i * 0.18
        y_bot = y_top - 0.15
        r_top = 1.00 + i * 0.08
        t = tube(r_top, r_top + 0.08, y_top, y_bot, segments=24,
                 a0=7 * math.pi / 6, a1=11 * math.pi / 6, name="fauld_back_%d" % i, material=bm)
        t.scale((1.0, 1.0, 0.72))
        meshes.append(_out(t))
    return meshes


def tasset(side):
    """Coxote dianteiro pendurado (frente da coxa)."""
    xc = LEG_R * side
    tag = "R" if side > 0 else "L"
    cols, rows = 9, 12
    grid = []
    for r in range(rows):
        h = r / (rows - 1)
        y = 1.35 - h * 0.55
        row = []
        for c in range(cols):
            t = c / (cols - 1)
            x = xc + (t - 0.5) * 0.62
            lat = math.sin(math.pi * t)
            z = 0.55 + 0.10 * lat + 0.05 * (1 - h)
            row.append((x, y, z))
        grid.append(row)
    m = thicken_surface(grid, 0.05, name="tasset_" + tag, material="steel")
    return _out(m)


# ==============================================================================
# Ombros / braços
# ==============================================================================

def pauldron(side):
    xc = ARM_R * side
    tag = "R" if side > 0 else "L"
    meshes = []
    d = dome(0.62, 0.34, 2.98, segments=22, name="pauldron_" + tag, material="steel")
    d.translate((xc, 0, 0))
    meshes.append(_out(d))
    lam = tube(0.62, 0.80, 2.72, 2.98, segments=24, name="pauldron_lame_" + tag, material="steel_dark")
    lam.translate((xc, 0, 0))
    meshes.append(_out(lam))
    return meshes


def rondel(side):
    tag = "R" if side > 0 else "L"
    d = _cup(0.24, 0.10, (ARM_R * side * 0.74, 2.82, 0.34), "+z", name="rondel_" + tag, material="steel")
    return _out(d)


def rerebrace(side, material="steel"):
    tag = "R" if side > 0 else "L"
    m = tube(0.60, 0.56, 2.05, 2.88, segments=20, name="rerebrace_" + tag, material=material)
    m.translate((ARM_R * side, 0, 0))
    return _out(m)


def couter(side, material="steel"):
    tag = "R" if side > 0 else "L"
    c = _cup(0.46, 0.40, (ARM_R * side, 1.95, -0.52), "-z", name="couter_" + tag, material=material)
    return _out(c)


def vambrace(side, material="steel"):
    tag = "R" if side > 0 else "L"
    m = tube(0.56, 0.52, 1.10, 1.95, segments=20, name="vambrace_" + tag, material=material)
    m.translate((ARM_R * side, 0, 0))
    return _out(m)


def gauntlet(side, material="steel_light"):
    tag = "R" if side > 0 else "L"
    prof = [(0.56, 1.18), (0.55, 1.08), (0.50, 1.00), (0.42, 0.95),
            (0.30, 0.92), (0.18, 0.905), (0.008, 0.90)]
    m = lathe(prof, segments=20, name="gauntlet_" + tag, material=material)
    m.translate((ARM_R * side, 0, 0))
    return _out(m)


def mail_sleeve(side):
    tag = "R" if side > 0 else "L"
    m = tube(0.62, 0.58, 1.12, 2.90, segments=20, name="mailsleeve_" + tag, material="mail")
    m.translate((ARM_R * side, 0, 0))
    return _out(m)


# ==============================================================================
# Pernas / pés
# ==============================================================================

def cuisse(side, material="steel"):
    tag = "R" if side > 0 else "L"
    m = tube(0.62, 0.56, 1.05, 1.95, segments=20, name="cuisse_" + tag, material=material)
    m.translate((LEG_R * side, 0, 0))
    return _out(m)


def poleyn(side, material="steel"):
    tag = "R" if side > 0 else "L"
    c = _cup(0.44, 0.36, (LEG_R * side, 1.0, 0.55), "+z", name="poleyn_" + tag, material=material)
    return _out(c)


def greave(side, material="steel"):
    tag = "R" if side > 0 else "L"
    m = tube(0.56, 0.50, 0.05, 0.95, segments=20, name="greave_" + tag, material=material)
    m.translate((LEG_R * side, 0, 0))
    return _out(m)


def sabaton(side, material="steel"):
    tag = "R" if side > 0 else "L"
    c = tube(0.27, 0.27, -0.075, 0.075, segments=16, cap_bottom=True, cap_top=True,
             name="sabaton_" + tag, material=material)
    c.rotate_x(math.pi / 2)          # eixo longo agora em +z
    c.scale((0.65, 0.55, 4.0))
    c.translate((LEG_R * side, 0.16, 0.10))
    return _out(c)


# ==============================================================================
# Elmos
# ==============================================================================

def helmet_european():
    meshes = []
    sk = dome(0.72, 0.82, 3.06, segments=28, name="helmet_skull", material="steel")
    meshes.append(_out(sk))
    vis = tube(0.64, 0.60, 3.34, 3.52, segments=28, a0=math.pi / 3, a1=2 * math.pi / 3,
               name="helmet_visor", material="steel_dark")
    meshes.append(_out(vis))
    bev = tube(0.62, 0.58, 3.10, 3.28, segments=28, a0=math.pi / 3.2, a1=2 * math.pi / 3.2,
               name="helmet_bevor", material="steel_dark")
    meshes.append(_out(bev))
    ng = tube(0.66, 0.80, 3.06, 3.30, segments=28, a0=7 * math.pi / 6, a1=11 * math.pi / 6,
              name="helmet_neck", material="steel")
    meshes.append(_out(ng))
    return meshes


def helmet_kabuto():
    meshes = []
    d = dome(0.70, 0.60, 3.22, segments=24, name="kabuto_hachi", material="lacquer_black")
    meshes.append(_out(d))
    for i in range(3):
        y_top = 3.18 - i * 0.14
        y_bot = y_top - 0.12
        r_top = 0.74 + i * 0.10
        t = tube(r_top, r_top + 0.10, y_top, y_bot, segments=24,
                 a0=math.pi / 6, a1=11 * math.pi / 6, name="shikoro_%d" % i, material="lacquer_black")
        meshes.append(_out(t))
    # kuwagata (chifres frontais dourados)
    for side in (1, -1):
        h = _cone(0.035, 0.34, (side * 0.20, 3.70, 0.52), "+y", name="kuwagata_%s" % ("R" if side > 0 else "L"), material="lacquer_gold")
        h.rotate_z(-side * 0.5)
        h.rotate_x(0.28)
        meshes.append(_out(h))
    return meshes


def menpo():
    meshes = []
    up = tube(0.60, 0.58, 3.38, 3.52, segments=24, a0=math.pi / 3, a1=2 * math.pi / 3,
              name="menpo_upper", material="lacquer_black")
    meshes.append(_out(up))
    lo = tube(0.62, 0.60, 3.08, 3.34, segments=24, a0=math.pi / 3, a1=2 * math.pi / 3,
              name="menpo_lower", material="lacquer_red")
    meshes.append(_out(lo))
    return meshes


def helmet_kulah_khud():
    meshes = []
    d = dome(0.70, 0.52, 3.24, segments=24, name="kulah_skull", material="steel")
    meshes.append(_out(d))
    sp = _cone(0.03, 0.20, (0, 3.74, 0), "+y", name="kulah_spike", material="steel")
    meshes.append(_out(sp))
    nb = box(-0.02, 0.02, 3.10, 3.44, 0.52, 0.60, name="kulah_nasal", material="steel")
    meshes.append(_out(nb))
    av = tube(0.68, 0.86, 3.06, 3.28, segments=24, a0=0, a1=2 * math.pi,
              name="kulah_aventail", material="mail")
    meshes.append(_out(av))
    return meshes


def helmet_ming():
    meshes = []
    d = dome(0.70, 0.56, 3.22, segments=24, name="ming_skull", material="steel_dark")
    meshes.append(_out(d))
    brim = tube(0.70, 0.92, 3.18, 3.24, segments=24, a0=0, a1=2 * math.pi,
                name="ming_brim", material="lacquer_black")
    meshes.append(_out(brim))
    sp = _cone(0.035, 0.18, (0, 3.76, 0), "+y", name="ming_spike", material="steel")
    meshes.append(_out(sp))
    return meshes


# ==============================================================================
# Peças específicas de variantes
# ==============================================================================

def lamellar_torso(y_top=2.70, y_bot=1.15, n=8, material="steel_dark",
                   back_material=None, scale_z=0.72, name="lamellar"):
    """Couraça lamelar: fileiras horizontais de lâminas sobrepostas (360°).

    Histórico: lamellar (lâminas atadas) foi o padrão na Ásia central/estepes
    (mongóis) e no leste asiático (Coreia), além de China e Japão.
    """
    meshes = []
    step = (y_top - y_bot) / n
    for i in range(n):
        yt = y_top - i * step
        yb = yt - step * 0.70
        r = 1.05
        t = tube(r, r + 0.03, yt, yb, segments=20,
                 a0=0.0, a1=math.pi, name="%s_front_%d" % (name, i), material=material)
        t.scale((1.0, 1.0, scale_z))
        meshes.append(_out(t))
    bm = back_material or material
    for i in range(n):
        yt = y_top - i * step
        yb = yt - step * 0.70
        r = 1.05
        t = tube(r, r + 0.03, yt, yb, segments=20,
                 a0=math.pi, a1=2 * math.pi, name="%s_back_%d" % (name, i), material=bm)
        t.scale((1.0, 1.0, scale_z))
        meshes.append(_out(t))
    return meshes


def helmet_mongol():
    """Elmo mongol (duulga): calota cônica, protetor de nuca lamelar, aro de pele."""
    meshes = []
    c = lathe([(0.58, 3.18), (0.34, 3.50), (0.05, 3.78)], segments=24,
              name="duulga_skull", material="steel")
    meshes.append(_out(c))
    for i in range(3):
        yt = 3.14 - i * 0.12
        yb = yt - 0.10
        t = tube(0.62 + i * 0.06, 0.68 + i * 0.06, yt, yb, segments=24,
                 a0=math.pi / 6, a1=11 * math.pi / 6, name="duulga_neck_%d" % i, material="steel_dark")
        meshes.append(_out(t))
    f = _cone(0.02, 0.12, (0, 3.80, 0), "+y", name="duulga_finial", material="steel")
    meshes.append(_out(f))
    b = tube(0.60, 0.66, 3.12, 3.18, segments=24, name="duulga_fur", material="fur")
    meshes.append(_out(b))
    return meshes


def helmet_korean():
    """Elmo coreano (Joseon): calota alta, aba larga, espigão e nuca de lâminas."""
    meshes = []
    d = dome(0.62, 0.72, 3.16, segments=24, name="korean_skull", material="steel_dark")
    meshes.append(_out(d))
    b = tube(0.62, 0.98, 3.12, 3.18, segments=24, name="korean_brim", material="lacquer_black")
    meshes.append(_out(b))
    sp = _cone(0.035, 0.20, (0, 3.88, 0), "+y", name="korean_spike", material="lacquer_gold")
    meshes.append(_out(sp))
    for i in range(2):
        yt = 3.08 - i * 0.12
        t = tube(0.62 + i * 0.06, 0.68 + i * 0.06, yt, yt - 0.10, segments=24,
                 a0=math.pi / 6, a1=11 * math.pi / 6, name="korean_neck_%d" % i, material="steel_dark")
        meshes.append(_out(t))
    return meshes


def shoulder_round(side, material="steel"):
    """Ombreira redonda simples (estilo estepe/leste asiático)."""
    tag = "R" if side > 0 else "L"
    d = dome(0.40, 0.22, 2.92, segments=18, name="shoulder_%s" % tag, material=material)
    d.translate((ARM_R * side * 0.9, 0, 0))
    return _out(d)


def sode(side):
    """Guardas de ombro retangulares (ō-sode), painel de lâminas sobrepostas."""
    meshes = []
    tag = "R" if side > 0 else "L"
    xc = ARM_R * side
    for i in range(4):
        y_mid = 2.90 - i * 0.24
        w = 0.54 - i * 0.02
        p = rounded_rect_plate(w, 0.24, 0.03, corner=0.04, segments=2,
                               name="sode_%d_%s" % (i, tag),
                               material="lacquer_red" if i % 2 == 0 else "lacquer_black")
        p.rotate_y(-side * 0.30)
        p.translate((xc * 1.30, y_mid, 0.30))
        meshes.append(_out(p))
    return meshes


def mirror_plates():
    meshes = []
    front = rounded_rect_plate(0.74, 0.98, 0.05, corner=0.18, bulge=0.10, segments=3,
                               name="mirror_front", material="steel")
    front.translate((0, 2.02, 0.57))
    meshes.append(_out(front))
    back = rounded_rect_plate(0.74, 0.98, 0.05, corner=0.18, bulge=0.10, segments=3,
                              name="mirror_back", material="steel")
    back.rotate_y(math.pi)
    back.translate((0, 2.02, -0.57))
    meshes.append(_out(back))
    for side in (1, -1):
        s = rounded_rect_plate(0.34, 0.72, 0.05, corner=0.12, bulge=0.06, segments=2,
                               name="mirror_side_%s" % ("R" if side > 0 else "L"), material="steel")
        s.rotate_y(side * math.pi / 2)
        s.translate((side * 1.08, 2.05, 0.0))
        meshes.append(_out(s))
    return meshes


def brigandine():
    """Couraça de brigandina (tecido com pinos de rebite aparentes)."""
    meshes = []
    g = _chest_grid(front=True, bulge_amp=0.07, y_top=2.70)
    plate = thicken_surface(g, 0.06, name="brigandine", material="fabric")
    meshes.append(_out(plate))
    # rebites: amostra da grade, deslocados para fora (+z)
    pts = []
    for r in range(1, len(g) - 1, 3):
        for c in range(1, len(g[0]) - 1, 3):
            x, y, z = g[r][c]
            pts.append((x, y, z + 0.06))
    meshes.append(_rivets(pts, size=0.075, name="brigandine_rivets", material="rivet"))
    return meshes


# ==============================================================================
# Montagem das variantes
# ==============================================================================

def underlayer_parts(material="mail"):
    """Roupa de base (malha/tecido) por baixo das placas — preenche as juntas.

    Histórico: a armadura de placas era vestida sobre cota de malha/gambeson;
    aqui isso também fecha os vãos do rig (axilas, cotovelos, joelhos, pescoço).
    """
    parts = []
    # tronco: prisma arredondado que envolve o bloco 2x1 (x ±1.08, z ±0.60)
    t = box_tube(1.08, 0.60, 0.16, 1.02, 3.02, name="under_torso", material=material, n=28)
    parts.append((_out(t), "Torso"))
    for side in (1, -1):
        tag = "R" if side > 0 else "L"
        a = box_tube(0.58, 0.58, 0.12, 1.02, 3.00, name="under_arm_" + tag,
                     material=material, n=20)
        a.translate((ARM_R * side, 0, 0))
        parts.append((_out(a), "Right Arm" if side > 0 else "Left Arm"))
        l = box_tube(0.58, 0.58, 0.12, 0.02, 1.98, name="under_leg_" + tag,
                     material=material, n=20)
        l.translate((LEG_R * side, 0, 0))
        parts.append((_out(l), "Right Leg" if side > 0 else "Left Leg"))
    return parts


def _armor_lists(side):
    """Braço + perna completos (lado dado) em aço."""
    tag = "R" if side > 0 else "L"
    return ([(rerebrace(side), "Right Arm" if side > 0 else "Left Arm"),
             (couter(side), "Right Arm" if side > 0 else "Left Arm"),
             (vambrace(side), "Right Arm" if side > 0 else "Left Arm"),
             (gauntlet(side), "Right Arm" if side > 0 else "Left Arm")],
            [(cuisse(side), "Right Leg" if side > 0 else "Left Leg"),
             (poleyn(side), "Right Leg" if side > 0 else "Left Leg"),
             (greave(side), "Right Leg" if side > 0 else "Left Leg"),
             (sabaton(side), "Right Leg" if side > 0 else "Left Leg")])


def build_variant(name):
    """Retorna lista de (Mesh, osso) na pose de descanso (bind)."""
    parts = []

    def add(mesh_list, bone):
        if isinstance(mesh_list, Mesh):
            mesh_list = [mesh_list]
        for m in mesh_list:
            parts.append((m, bone))

    if name == "european":
        for m, b in underlayer_parts("mail"):
            add(m, b)
        add(cuirass_front(), "Torso")
        add(cuirass_back(), "Torso")
        add(gorget(), "Torso")
        add(fauld(), "Torso")
        for s in (1, -1):
            add(tasset(s), "Torso")
            add(pauldron(s), "Torso")
            add(rondel(s), "Torso")
        add(helmet_european(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(rerebrace(s), bone_arm)
            add(couter(s), bone_arm)
            add(vambrace(s), bone_arm)
            add(gauntlet(s), bone_arm)
            add(cuisse(s), bone_leg)
            add(poleyn(s), bone_leg)
            add(greave(s), bone_leg)
            add(sabaton(s), bone_leg)

    elif name == "japanese":
        for m, b in underlayer_parts("silk"):
            add(m, b)
        add(cuirass_front(), "Torso")          # dō
        add(cuirass_back(), "Torso")
        add(fauld(material="lacquer_black", back_material="lacquer_black"), "Torso")  # kusazuri
        add(gorget(), "Torso")                 # nodowa
        for s in (1, -1):
            add(sode(s), "Torso")
        add(helmet_kabuto(), "Head")
        add(menpo(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(rerebrace(s, material="lacquer_black"), bone_arm)
            add(couter(s, material="lacquer_black"), bone_arm)
            add(vambrace(s, material="lacquer_black"), bone_arm)
            add(gauntlet(s, material="lacquer_black"), bone_arm)
            add(cuisse(s, material="lacquer_black"), bone_leg)
            add(poleyn(s, material="lacquer_black"), bone_leg)
            add(greave(s, material="lacquer_red"), bone_leg)   # suneate
            add(sabaton(s, material="lacquer_black"), bone_leg)

    elif name == "persian":
        for m, b in underlayer_parts("mail"):
            add(m, b)
        add(mirror_plates(), "Torso")
        add(fauld(material="mail", back_material="mail"), "Torso")
        add(helmet_kulah_khud(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(mail_sleeve(s), bone_arm)
            add(gauntlet(s, material="steel"), bone_arm)
            add(greave(s), bone_leg)
            add(sabaton(s), bone_leg)

    elif name == "ming":
        for m, b in underlayer_parts("fabric"):
            add(m, b)
        add(brigandine(), "Torso")
        add(fauld(material="fabric", back_material="fabric"), "Torso")
        add(helmet_ming(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(vambrace(s), bone_arm)
            add(gauntlet(s, material="steel_light"), bone_arm)
            add(greave(s), bone_leg)
            add(sabaton(s), bone_leg)

    elif name == "mongol":
        for m, b in underlayer_parts("leather"):
            add(m, b)
        add(lamellar_torso(material="steel_dark"), "Torso")
        add(helmet_mongol(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(shoulder_round(s, material="steel_dark"), "Torso")
            add(vambrace(s), bone_arm)
            add(gauntlet(s, material="steel_light"), bone_arm)
            add(cuisse(s, material="leather"), bone_leg)
            add(greave(s), bone_leg)
            add(sabaton(s), bone_leg)

    elif name == "korean":
        for m, b in underlayer_parts("silk"):
            add(m, b)
        add(lamellar_torso(material="lacquer_red", back_material="steel_dark"), "Torso")
        add(helmet_korean(), "Head")
        for s in (1, -1):
            bone_arm = "Right Arm" if s > 0 else "Left Arm"
            bone_leg = "Right Leg" if s > 0 else "Left Leg"
            add(shoulder_round(s, material="steel"), "Torso")
            add(vambrace(s, material="steel"), bone_arm)
            add(gauntlet(s, material="steel_light"), bone_arm)
            add(cuisse(s, material="steel"), bone_leg)
            add(greave(s, material="lacquer_red"), bone_leg)
            add(sabaton(s), bone_leg)

    else:
        raise ValueError("variante desconhecida: %s" % name)

    return parts


VARIANTS = ["european", "japanese", "persian", "ming", "mongol", "korean"]
