#!/usr/bin/env python3
"""make_viewer.py — Gera frames de preview (turntable + animações) e o HTML do visualizador.

Renderiza, com o próprio rasterizador, sequências de imagens por variante:
  * turntable (giro 360°),
  * idle e walk (animação real, com skinning aplicado pelo motor de rig).

Depois escreve export/index.html (visualizador interativo). Sirva a pasta export/
com um servidor estático para abrir no navegador.
"""

import os
import math
import sys

from engine import armor_models as A
from engine.animation import make_idle, make_walk, make_run, make_attack
from engine.rig import pose_parts
from engine.render import Camera, Renderer
from engine.mesh import box
from build import mat_color, LIGHT, mannequin_boxes

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "export")
VIEWER = os.path.join(OUT, "viewer")

W, H = 320, 440
BODY_COLOR = (58, 62, 74)

_MANN_BONE = {"Torso": "Torso", "Head": "Head", "RightArm": "Right Arm",
              "LeftArm": "Left Arm", "RightLeg": "Right Leg", "LeftLeg": "Left Leg"}


def mannequin_parts():
    parts = []
    for b in mannequin_boxes():
        parts.append((b, _MANN_BONE[b.name]))
    return parts


def render_frame(parts, mann, pose, root_pos, camera):
    r = Renderer(W, H)
    mann_posed = pose_parts(mann, pose, root_pos)
    for m, _ in mann_posed:
        r.draw_mesh(camera, m, BODY_COLOR, LIGHT)
    posed = pose_parts(parts, pose, root_pos)
    for m, _ in posed:
        r.draw_mesh(camera, m, mat_color(m.material), LIGHT)
    return r


def main():
    os.makedirs(VIEWER, exist_ok=True)
    idle = make_idle()
    walk = make_walk()
    run = make_run()
    attack = make_attack()

    modes = {"turntable": 16, "idle": 16, "walk": 16, "run": 16, "attack": 16}

    only = sys.argv[1:] if len(sys.argv) > 1 else A.VARIANTS
    variants = [v for v in A.VARIANTS if v in only]

    for name in variants:
        parts = A.build_variant(name)
        for m, _ in parts:
            m.triangulate()
        mann = mannequin_parts()
        vdir = os.path.join(VIEWER, name)
        os.makedirs(vdir, exist_ok=True)

        # turntable
        R = 4.6
        for i in range(modes["turntable"]):
            a = 2 * math.pi * i / modes["turntable"]
            cam = Camera((R * math.sin(a), 2.0, R * math.cos(a)), (0, 2.0, 0), fov=38)
            r = render_frame(parts, mann, {}, None, cam)
            r.save_png(os.path.join(vdir, "turntable_%02d.png" % i))

        # animações (amostra uniforme)
        for mname, clip in (("idle", idle), ("walk", walk), ("run", run), ("attack", attack)):
            n = modes[mname]
            for i in range(n):
                k = int(round(i * (len(clip) - 1) / (n - 1)))
                rp, pose = clip[k]
                cam = Camera((3.4, 2.4, 3.4), (0, 2.0, 0), fov=38)
                r = render_frame(parts, mann, pose, rp, cam)
                r.save_png(os.path.join(vdir, "%s_%02d.png" % (mname, i)))
        print("[viewer] %s pronto" % name)

    write_html()


HTML = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Armadura R6 — Visualizador 3D</title>
<style>
  :root { --bg:#0e1117; --panel:#161b24; --line:#232a37; --txt:#d7dee9; --dim:#8a94a6; --acc:#e0b14a; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--txt); font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
         min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
  header { width: 100%; padding: 18px 20px 10px; text-align: center; }
  header h1 { font-size: 20px; letter-spacing: .3px; }
  header p { color: var(--dim); font-size: 13px; margin-top: 4px; }
  .wrap { width: min(940px, 96vw); display: grid; grid-template-columns: 200px 1fr; gap: 16px; padding: 10px 0 30px; }
  @media (max-width: 640px){ .wrap { grid-template-columns: 1fr; } }
  .side { display: flex; flex-direction: column; gap: 18px; }
  .group { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }
  .group h2 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--dim); margin-bottom: 8px; }
  .btn { display: block; width: 100%; text-align: left; padding: 8px 10px; margin: 4px 0; border-radius: 8px;
         border: 1px solid transparent; background: transparent; color: var(--txt); cursor: pointer; font-size: 14px; }
  .btn:hover { background: #1c2230; }
  .btn.active { background: #22304a; border-color: var(--acc); color: #fff; }
  .stage { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px;
           display: flex; flex-direction: column; align-items: center; }
  #frame { max-width: 100%; max-height: 68vh; border-radius: 8px; image-rendering: auto; background: #000; }
  .transport { width: 100%; display: flex; align-items: center; gap: 12px; margin-top: 12px; }
  .transport button { background: #1c2230; color: var(--txt); border: 1px solid var(--line); border-radius: 8px;
                      width: 40px; height: 34px; cursor: pointer; font-size: 16px; }
  .transport button:hover { background: #27324a; }
  input[type=range] { flex: 1; accent-color: var(--acc); }
  #counter { color: var(--dim); font-size: 12px; min-width: 44px; text-align: right; }
  .hint { color: var(--dim); font-size: 12px; margin-top: 10px; text-align: center; }
  .links a { color: var(--acc); text-decoration: none; font-size: 13px; display: block; margin: 4px 0; }
  .links a:hover { text-decoration: underline; }
</style>
</head>
<body>
<header>
  <h1>⚔️ Armadura de Ferro Completa — rig R6 do Roblox</h1>
  <p>4 variantes históricas · turntable 360° + animações (Idle / Walk) renderizadas pelo motor próprio (sem Blender/Cascadeur)</p>
</header>
<div class="wrap">
  <aside class="side">
    <div class="group">
      <h2>Variante</h2>
      <div id="variants"></div>
    </div>
    <div class="group">
      <h2>Visualização</h2>
      <div id="modes"></div>
    </div>
    <div class="group links">
      <h2>Arquivos reais</h2>
      <a href="gltf/european.glb" download>gltf/european.glb (rig + anim)</a>
      <a href="obj/european.obj" download>obj/european.obj</a>
      <a href="lua/install_european.luau" download>lua/install_european.luau</a>
      <a href="bvh/r6_walk.bvh" download>bvh/r6_walk.bvh</a>
    </div>
  </aside>
  <main class="stage">
    <img id="frame" alt="preview">
    <div class="transport">
      <button id="play">▶</button>
      <input type="range" id="scrub" min="0" max="15" value="0" step="1">
      <span id="counter">0/15</span>
    </div>
    <div class="hint">Espaço = play/pause · ←/→ = quadro · clique nas opções ao lado</div>
  </main>
</div>
<script>
const VARIANTS = [['european','Europeia (full plate)'],['japanese','Samurai (ō-yoroi)'],
                  ['persian','Chahar-aina (4 espelhos)'],['ming','Brigandine Ming'],
                  ['mongol','Mongol (lamellar)'],['korean','Coreana (Joseon)']];
const MODES = [['turntable','🔄 Turntable 360°'],['idle','🧍 Idle (respiração)'],
               ['walk','🚶 Walk (caminhada)'],['run','🏃 Run (corrida)'],['attack','⚔️ Attack (golpe)']];
let v = 'european', m = 'turntable', i = 0, playing = true, timer = null;
const N = 16;
const img = document.getElementById('frame');
const scrub = document.getElementById('scrub');
const counter = document.getElementById('counter');
const playBtn = document.getElementById('play');

const vbox = document.getElementById('variants');
VARIANTS.forEach(([id,label]) => {
  const b = document.createElement('button');
  b.className = 'btn' + (id===v ? ' active' : '');
  b.textContent = label; b.dataset.v = id;
  b.addEventListener('click', ()=>{ v=id; i=0; update();
    document.querySelectorAll('#variants .btn').forEach(x=>x.classList.toggle('active', x.dataset.v===v)); });
  vbox.appendChild(b);
});
const mbox = document.getElementById('modes');
MODES.forEach(([id,label]) => {
  const b = document.createElement('button');
  b.className = 'btn' + (id===m ? ' active' : '');
  b.textContent = label; b.dataset.m = id;
  b.addEventListener('click', ()=>{ m=id; i=0; update();
    document.querySelectorAll('#modes .btn').forEach(x=>x.classList.toggle('active', x.dataset.m===m)); });
  mbox.appendChild(b);
});

function src(){ return 'viewer/' + v + '/' + m + '_' + String(i).padStart(2,'0') + '.png'; }
function update(){
  img.src = src();
  scrub.value = i;
  counter.textContent = (i+1) + '/' + N;
}
function tick(){ i = (i + 1) % N; update(); }
function setPlay(p){
  playing = p; playBtn.textContent = p ? '⏸' : '▶';
  if (timer){ clearInterval(timer); timer = null; }
  if (p){ timer = setInterval(tick, m==='turntable' ? 110 : 66); }
}
playBtn.addEventListener('click', ()=>setPlay(!playing));
scrub.addEventListener('input', e => { i = +e.target.value; update(); });
window.addEventListener('keydown', e => {
  if (e.code === 'Space'){ e.preventDefault(); setPlay(!playing); }
  else if (e.code === 'ArrowRight'){ i = (i+1)%N; setPlay(false); update(); }
  else if (e.code === 'ArrowLeft'){ i = (i-1+N)%N; setPlay(false); update(); }
});
update(); setPlay(true);
</script>
</body>
</html>
"""


def write_html():
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(HTML)
    print("[viewer] index.html escrito")


if __name__ == "__main__":
    main()
