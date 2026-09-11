"""animation.py — Motor de animação próprio (substituto do Cascadeur para esta tarefa).

Gera ciclos de animação (idle / andar / correr) com:
  * marcha compasso de perna rígida (natural no R6, que não tem joelho),
  * movimento vertical balístico do centro de massa (assinatura do Cascadeur),
  * braços em oposição às pernas, contrarrotação de ombros/quadril,
  * estabilização da cabeça (mantém o olhar à frente).

Convenção interna: rotações locais (rx, ry, rz) com R = Rz·Ry·Rx (X aplicado primeiro),
igual a CFrame.fromEulerAnglesXYZ do Roblox. Ângulo "para frente" positivo = -rx.
"""

import math
from . import math3d as m3

FPS = 30


def _mk(leg_amp, arm_amp, lean, bob, twist, sway, head_nod, frames, T):
    """Constrói um ciclo genérico de marcha (lista de (root_pos, pose_dict))."""
    clip = []
    for i in range(frames):
        ph = i / (frames - 1)          # 0..1
        t = ph * 2.0 * math.pi
        # pernas em oposição
        th_r = leg_amp * math.sin(t)
        th_l = -th_r
        # braços em oposição às pernas
        ar_r = -arm_amp * math.sin(t)
        ar_l = arm_amp * math.sin(t)
        pose = {
            "Right Leg": (-th_r, 0.0, 0.0),
            "Left Leg":  (-th_l, 0.0, 0.0),
            "Right Arm": (-ar_r, 0.0, 0.0),
            "Left Arm":  (-ar_l, 0.0, 0.0),
            "Torso": (lean, twist * math.sin(t), sway * math.sin(t)),
            "Head": (head_nod * math.sin(t + math.pi), -twist * math.sin(t), 0.0),
        }
        # centro de massa: mais alto quando as pernas se cruzam (2 máximos/ciclo)
        y_bob = bob * math.cos(2.0 * t)
        root_pos = (0.0, 1.0 + y_bob, 0.0)
        clip.append((root_pos, pose))
    return clip


def make_walk(frames=31, T=1.0):
    return _mk(leg_amp=0.62, arm_amp=0.50, lean=0.12, bob=0.05,
               twist=0.06, sway=0.03, head_nod=0.05, frames=frames, T=T)


def make_run(frames=21, T=0.7):
    return _mk(leg_amp=0.95, arm_amp=0.85, lean=0.30, bob=0.09,
               twist=0.10, sway=0.05, head_nod=0.06, frames=frames, T=T)


def make_attack(frames=25, T=0.85):
    """Golpe: os dois braços sobem e descem à frente, com inclinação do tronco."""
    clip = []
    for i in range(frames):
        ph = i / (frames - 1)
        t = ph * 2.0 * math.pi
        arm_rx = -1.2 * math.sin(t) - 0.3
        lean = 0.22 * math.sin(t)
        clip.append(((0.0, 1.0 + 0.02 * math.cos(t), 0.0), {
            "Right Arm": (arm_rx, 0.0, 0.0),
            "Left Arm": (arm_rx, 0.0, 0.0),
            "Torso": (lean, 0.0, 0.0),
            "Head": (0.08 * math.sin(t + math.pi), 0.0, 0.0),
            "Right Leg": (0.15 * math.sin(t), 0.0, 0.0),
            "Left Leg": (-0.15 * math.sin(t), 0.0, 0.0),
        }))
    return clip


def make_block(frames=25, T=0.85):
    """Postura de guarda/bloqueio: braços à frente, leve recuo do tronco."""
    clip = []
    for i in range(frames):
        ph = i / (frames - 1)
        t = ph * 2.0 * math.pi
        arm_rx = -1.2 + 0.06 * math.sin(t)
        clip.append(((0.0, 1.0 + 0.01 * math.sin(t), 0.0), {
            "Right Arm": (arm_rx, 0.0, 0.0),
            "Left Arm": (arm_rx, 0.0, 0.0),
            "Torso": (-0.08 + 0.02 * math.sin(t), 0.0, 0.0),
            "Head": (0.03 * math.sin(t), 0.0, 0.0),
        }))
    return clip


def make_idle(frames=61, T=2.0):
    clip = []
    for i in range(frames):
        ph = i / (frames - 1)
        t = ph * 2.0 * math.pi
        pose = {
            "Right Arm": (-0.03 * math.sin(t), 0.0, 0.0),
            "Left Arm":  (0.03 * math.sin(t), 0.0, 0.0),
            "Right Leg": (0.02 * math.sin(t), 0.0, 0.0),
            "Left Leg":  (-0.02 * math.sin(t), 0.0, 0.0),
            "Torso": (0.02 * math.sin(t), 0.0, 0.01 * math.sin(t)),
            "Head": (0.02 * math.sin(t * 0.5), 0.0, 0.0),
        }
        root_pos = (0.0, 1.0 + 0.01 * math.sin(t), 0.0)
        clip.append((root_pos, pose))
    return clip


# ------------------------------------------------------------------------------
# Conversões para exportação
# ------------------------------------------------------------------------------

def mat_to_quat(m):
    """Matriz 3x3 (linhas) -> quaternion (x, y, z, w). Método de Shepperd."""
    m00, m01, m02 = m[0]
    m10, m11, m12 = m[1]
    m20, m21, m22 = m[2]
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        return ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s)
    if m00 >= m11 and m00 >= m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        return (0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
    if m11 >= m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        return ((m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s)
    s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
    return ((m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s)


def local_quats(skeleton, pose):
    """Quaternions locais (x,y,z,w) por junta, dado um dict de pose."""
    out = {}
    for j in skeleton.joints:
        if j.parent >= 0 and j.name in pose:
            rx, ry, rz = pose[j.name]
            m = m3.euler_xyz(rx, ry, rz)
            out[j.name] = mat_to_quat(m)
        else:
            out[j.name] = (0.0, 0.0, 0.0, 1.0)
    return out


# ------------------------------------------------------------------------------
# Exportador BVH
# ------------------------------------------------------------------------------

def _write_hierarchy(f, skeleton, idx, depth):
    j = skeleton.joints[idx]
    pad = "\t" * depth
    is_root = j.parent < 0
    f.write("%s%s %s\n" % (pad, "ROOT" if is_root else "JOINT", j.name))
    f.write("%s{\n" % pad)
    f.write("%s\tOFFSET %.6f %.6f %.6f\n" % (pad, j.offset[0], j.offset[1], j.offset[2]))
    if is_root:
        f.write("%s\tCHANNELS 6 Xposition Yposition Zposition Zrotation Yrotation Xrotation\n" % pad)
    else:
        f.write("%s\tCHANNELS 3 Zrotation Yrotation Xrotation\n" % pad)
    children = [k for k, c in enumerate(skeleton.joints) if c.parent == idx]
    if children:
        for c in children:
            _write_hierarchy(f, skeleton, c, depth + 1)
    else:
        f.write("%s\tEnd Site\n%s\t{\n%s\t\tOFFSET 0.0 0.0 0.0\n%s\t}\n" % (pad, pad, pad, pad))
    f.write("%s}\n" % pad)


def _frame_order(skeleton):
    """Ordem DFS das juntas (igual à hierarquia BVH)."""
    order = []
    def rec(i):
        order.append(i)
        for k, c in enumerate(skeleton.joints):
            if c.parent == i:
                rec(k)
    rec(0)
    return order


def write_bvh(path, skeleton, clip, fps=FPS):
    order = _frame_order(skeleton)
    with open(path, "w") as f:
        f.write("HIERARCHY\n")
        _write_hierarchy(f, skeleton, 0, 0)
        f.write("MOTION\n")
        f.write("Frames: %d\n" % len(clip))
        f.write("Frame Time: %.6f\n" % (1.0 / fps))
        for (root_pos, pose) in clip:
            vals = []
            for i in order:
                j = skeleton.joints[i]
                if j.parent < 0:
                    vals += [root_pos[0], root_pos[1], root_pos[2], 0.0, 0.0, 0.0]
                else:
                    rx, ry, rz = pose.get(j.name, (0.0, 0.0, 0.0))
                    vals += [rz, ry, rx]  # canais: Z Y X
            f.write(" ".join("%.6f" % v for v in vals) + "\n")


# ------------------------------------------------------------------------------
# Exportador Lua (KeyframeSequence do Roblox Studio)
# ------------------------------------------------------------------------------

def write_lua_animations(path, skeleton, clips):
    """Gera um script Lua que cria KeyframeSequences (idle/walk/run) e toca no Humanoid."""
    motor_of = {j.name: (j.r6_motor or j.name) for j in skeleton.joints if j.parent >= 0}
    lines = []
    lines.append("-- Animacoes geradas pelo motor de animacao proprio (estilo Cascadeur)")
    lines.append("-- Cole no Roblox Studio (Command Bar) com um personagem R6 selecionado.")
    lines.append("local character = script.Parent")
    lines.append("if not character:FindFirstChildOfClass('Humanoid') then")
    lines.append("    character = game.Players.LocalPlayer.Character or workspace:FindFirstChildOfClass('Model')")
    lines.append("end")
    lines.append("local humanoid = character:FindFirstChildOfClass('Humanoid')")
    lines.append("local animator = humanoid:WaitForChild('Animator')")
    lines.append("")
    lines.append("local function build(name, frames, priority)")
    lines.append("    local kfs = Instance.new('KeyframeSequence')")
    lines.append("    kfs.Name = name")
    lines.append("    kfs.Loop = true")
    lines.append("    kfs.Priority = priority")
    lines.append("    for fi, fr in ipairs(frames) do")
    lines.append("        local key = Instance.new('Keyframe')")
    lines.append("        key.Time = (fi - 1) / (30)")
    lines.append("        key.Parent = kfs")
    lines.append("        for motor, angles in pairs(fr) do")
    lines.append("            local pose = Instance.new('Pose')")
    lines.append("            pose.Name = motor")
    lines.append("            pose.CFrame = CFrame.Angles(angles[1], angles[2], angles[3])")
    lines.append("            pose.Parent = key")
    lines.append("        end")
    lines.append("    end")
    lines.append("    return kfs")
    lines.append("end")
    lines.append("")
    for name, clip, prio in clips:
        lines.append("local frames_%s = {" % name)
        for (root_pos, pose) in clip:
            entries = []
            for jname, ang in pose.items():
                if abs(ang[0]) > 1e-4 or abs(ang[1]) > 1e-4 or abs(ang[2]) > 1e-4:
                    entries.append("['%s'] = {%.5f, %.5f, %.5f}" % (motor_of[jname], ang[0], ang[1], ang[2]))
            lines.append("    {" + ", ".join(entries) + "},")
        lines.append("}")
        lines.append("local kfs_%s = build('%s', frames_%s, Enum.AnimationPriority.%s)" % (name, name, name, prio))
        lines.append("local anim_%s = animator:LoadAnimation(kfs_%s)" % (name, name))
        lines.append("")
    lines.append("-- toca a caminhada por padrao; troque por anim_idle / anim_run")
    lines.append("anim_walk:Play()")
    lines.append("print('Animacoes carregadas: idle, walk, run')")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
