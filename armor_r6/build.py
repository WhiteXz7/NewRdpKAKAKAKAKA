#!/usr/bin/env python3
"""build.py — Orquestrador: gera todos os artefatos da armadura R6.

Executa (sem dependências externas, só biblioteca padrão):
  1. modelagem procedural das 4 variantes históricas (substituto do Blender),
  2. exportação OBJ + MTL (espaço-mundo e "baked" para solda no Roblox),
  3. exportação glTF 2.0 (.glb) com esqueleto R6 + skinning + animações,
  4. exportação BVH das animações (para Cascadeur),
  5. scripts Lua de instalação (solda) e animações (KeyframeSequence),
  6. previews PNG renderizados pelo rasterizador próprio.

Uso:
    python3 build.py
"""

import os
import json

from engine import armor_models as A
from engine.animation import make_walk, make_run, make_idle, write_bvh, write_lua_animations, FPS
from engine.gltf import build_glb
from engine.mesh import write_obj, write_mtl, MTL_PALETTE, box
from engine.rig import build_r6_skeleton, R6_PART_CENTERS, R6_MOTORS
from engine.render import Camera, Renderer

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "export")
os.makedirs(os.path.join(OUT, "obj"), exist_ok=True)
os.makedirs(os.path.join(OUT, "gltf"), exist_ok=True)
os.makedirs(os.path.join(OUT, "bvh"), exist_ok=True)
os.makedirs(os.path.join(OUT, "lua"), exist_ok=True)
os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)

LIGHT = (0.45, 0.85, 0.65)


def mat_color(name):
    kd = MTL_PALETTE.get(name, MTL_PALETTE["steel"])[0]
    return (int(kd[0] * 255), int(kd[1] * 255), int(kd[2] * 255))


def mannequin_boxes():
    """Blocos do R6 (para visualizar o manequim por baixo da armadura)."""
    body = []
    body.append(box(-1.0, 1.0, 1.0, 3.0, -0.5, 0.5, name="Torso", material="steel_dark"))
    body.append(box(-0.6, 0.6, 3.0, 4.2, -0.6, 0.6, name="Head", material="steel_dark"))
    body.append(box(1.0, 2.0, 1.0, 3.0, -0.5, 0.5, name="RightArm", material="steel_dark"))
    body.append(box(-2.0, -1.0, 1.0, 3.0, -0.5, 0.5, name="LeftArm", material="steel_dark"))
    body.append(box(0.0, 1.0, 0.0, 2.0, -0.5, 0.5, name="RightLeg", material="steel_dark"))
    body.append(box(-1.0, 0.0, 0.0, 2.0, -0.5, 0.5, name="LeftLeg", material="steel_dark"))
    for b in body:
        b.triangulate()
    return body


BODY_COLOR = (58, 62, 74)


def render_meshes(parts, camera, size=(480, 640), with_body=True):
    r = Renderer(size[0], size[1])
    if with_body:
        for b in mannequin_boxes():
            r.draw_mesh(camera, b, BODY_COLOR, LIGHT)
    for m, _ in parts:
        r.draw_mesh(camera, m, mat_color(m.material), LIGHT)
    return r


def render_grid(variants_parts, path):
    """Grade 2x2 com vista 3/4 de cada variante."""
    w, h = 480, 640
    r = Renderer(w * 2, h * 2)
    cam = Camera((3.4, 2.6, 3.4), (0, 2.0, 0), fov=38)
    for i, parts in enumerate(variants_parts):
        col, row = i % 2, i // 2
        r.set_viewport(col * w, row * h, (col + 1) * w, (row + 1) * h)
        for b in mannequin_boxes():
            r.draw_mesh(cam, b, BODY_COLOR, LIGHT)
        for m, _ in parts:
            r.draw_mesh(cam, m, mat_color(m.material), LIGHT)
    r.set_viewport(0, 0, w * 2, h * 2)
    r.save_png(path)


def write_glb(path, parts, clips):
    data = build_glb(parts, clips, FPS, os.path.basename(path))
    with open(path, "wb") as f:
        f.write(data)


def write_baked_obj(path, parts):
    """OBJ com geometria rebatida para o espaço local de cada parte do R6
    (pronto para soldar com C0=C1=identidade)."""
    baked = []
    for m, bone in parts:
        c = R6_PART_CENTERS[bone]
        n = m.copy()
        n.transform(lambda v: (v[0] - c[0], v[1] - c[1], v[2] - c[2]))
        baked.append(n)
    write_obj(path, baked)


def write_lua_install(path, parts):
    """Script de solda: mapeia cada peça da armadura para sua parte do R6."""
    mapping = {}
    for m, bone in parts:
        mapping.setdefault(m.name, bone)
    lines = [
        "-- Instalador da armadura no rig R6 (gerado automaticamente).",
        "-- 1) Importe o .obj *_roblox_baked no Roblox Studio.",
        "-- 2) Renomeie o Model importado para 'Armor'.",
        "-- 3) Coloque este script DENTRO do model 'Armor' (como Script).",
        "-- 4) Ajuste CHARACTER_NAME para o nome do seu personagem R6 no Workspace.",
        "",
        "local CHARACTER_NAME = 'SeuPersonagemR6'",
        "local armor = script.Parent",
        "local character = workspace:FindFirstChild(CHARACTER_NAME)",
        "if not character then",
        "    for _, m in ipairs(workspace:GetChildren()) do",
        "        if m:FindFirstChildOfClass('Humanoid') and not m:FindFirstChild('ArmorInstalled') then",
        "            character = m; break",
        "        end",
        "    end",
        "end",
        "if not character then error('Personagem R6 nao encontrado no Workspace') end",
        "",
        "local MAPPING = {",
    ]
    for pname, bone in sorted(mapping.items()):
        lines.append('    ["%s"] = "%s",' % (pname, bone))
    lines += [
        "}",
        "",
        "for _, part in ipairs(armor:GetDescendants()) do",
        "    if not part:IsA('BasePart') then continue end",
        "    local targetName = MAPPING[part.Name]",
        "    if not targetName then continue end",
        "    local target = character:FindFirstChild(targetName)",
        "    if not target or not target:IsA('BasePart') then continue end",
        "    local weld = Instance.new('Weld')",
        "    weld.Name = 'Armor_' .. part.Name",
        "    weld.Part0 = target",
        "    weld.Part1 = part",
        "    weld.C0 = CFrame.new()  -- geometria ja vem no espaco local da parte",
        "    weld.C1 = CFrame.new()",
        "    weld.Parent = part",
        "    part.Anchored = false",
        "    part.CanCollide = false",
        "end",
        "",
        "local tag = Instance.new('BoolValue')",
        "tag.Name = 'ArmorInstalled'",
        "tag.Parent = character",
        "print('Armadura instalada com sucesso!')",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    clips = {"idle": make_idle(), "walk": make_walk(), "run": make_run()}
    skeleton = build_r6_skeleton()

    # BVH por clipe (esqueleto em descanso + animação)
    for name, clip in clips.items():
        write_bvh(os.path.join(OUT, "bvh", "r6_%s.bvh" % name), skeleton, clip)

    # Lua de animações
    clip_list = [("idle", clips["idle"], "Idle"),
                 ("walk", clips["walk"], "Movement"),
                 ("run", clips["run"], "Movement")]
    write_lua_animations(os.path.join(OUT, "lua", "animations.luau"), skeleton, clip_list)

    # MTL único
    write_mtl(os.path.join(OUT, "obj", "armor.mtl"))

    # manequim (para Blender)
    mannequin = mannequin_boxes()
    write_obj(os.path.join(OUT, "obj", "r6_mannequin.obj"), mannequin)

    variants_parts = []
    manifest = {}
    for name in A.VARIANTS:
        parts = A.build_variant(name)
        for m, _ in parts:
            m.triangulate()
        variants_parts.append(parts)

        tris = sum(m.n_tris() for m, _ in parts)
        manifest[name] = {"meshes": len(parts), "triangles": tris}

        # previews
        cams = {"front": Camera((0, 2.0, 4.6), (0, 2.0, 0), fov=38),
                "side": Camera((4.6, 2.0, 0), (0, 2.0, 0), fov=38),
                "threequarter": Camera((3.4, 2.6, 3.4), (0, 2.0, 0), fov=38)}
        for view, cam in cams.items():
            r = render_meshes(parts, cam)
            r.save_png(os.path.join(OUT, "previews", "%s_%s.png" % (name, view)))

        # OBJ mundo + baked + glb
        write_obj(os.path.join(OUT, "obj", "%s.obj" % name), [m for m, _ in parts])
        write_baked_obj(os.path.join(OUT, "obj", "%s_roblox_baked.obj" % name), parts)
        write_glb(os.path.join(OUT, "gltf", "%s.glb" % name), parts, clips)

        # Lua install
        write_lua_install(os.path.join(OUT, "lua", "install_%s.luau" % name), parts)

        print("[%s] %d peças, %d triângulos" % (name, len(parts), tris))

    # grade comparativa
    render_grid(variants_parts, os.path.join(OUT, "previews", "all_variants.png"))

    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump({"fps": FPS, "variants": manifest,
                   "part_centers": {k: list(v) for k, v in R6_PART_CENTERS.items()},
                   "motors": R6_MOTORS}, f, indent=2)

    print("\nArtefatos gerados em:", OUT)


if __name__ == "__main__":
    main()
