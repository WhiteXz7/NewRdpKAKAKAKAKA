# Armadura de Ferro Completa + Variações Mundiais — para o rig R6 do Roblox

Como **Blender e Cascadeur não estão disponíveis** neste ambiente, este projeto
implementa, em **Python puro (só biblioteca padrão, sem internet e sem dependências)**,
os dois substitutos:

| Ferramenta original | Substituição aqui | Arquivo |
|---|---|---|
| **Blender** (modelagem) | Motor de modelagem procedural: primitivas + superfícies espessadas + normais + orientação de faces | `engine/mesh.py`, `engine/armor_models.py` |
| **Blender** (rigging) | Esqueleto R6 + skinning (junta por peça) | `engine/rig.py`, `engine/gltf.py` |
| **Cascadeur** (animação) | Motor de animação por ciclos (marcha, balística do centro de massa, braços em oposição) | `engine/animation.py` |
| **Viewport/Preview** | Rasterizador de software (Gouraud + z-buffer) que gera PNG | `engine/render.py` |

O resultado é um conjunto de **artefatos 3D reais e importáveis** no Roblox Studio,
no Blender e no Cascadeur (quando você tiver acesso a eles).

---

## O que foi modelado (baseado em pesquisa histórica)

Ver **`PESQUISA_ARMADURAS.md`** para a pesquisa completa com fontes.

### 1. Armadura de placas completa europeia (séc. XV) — *a armadura de ferro completa*
Peças reais, todas presentes no modelo:
elmo fechado (com visor, barbote e protetor de nuca), gorget, pauldrons + rondéis (besagews),
rerebrace, couter, vambrace, gauntlet (manopla), cuirass (peitoral + dorsal), fauld
(fraldão de lâminas), tassets, culet, cuisses, poleyn, greaves e sabatons — vestida
sobre **cota de malha** (underlayer) nas juntas, como era historicamente.

### 2. Variações pelo mundo
- **Japão (samurai, ō-yoroi/tōsei-gusoku):** kabuto com shikoro, menpō, kuwagata, dō,
  kusazuri, ō-sode, kote, suneate — com laca vermelha/preta/dourada.
- **Pérsia/Índia/Otomanos (chahar-aina, "quatro espelhos"):** kulah khud (elmo com espigão
  e nasal), 4 placas-espelho sobre cota de malha (zirah), bazu-band, dastana.
- **China (brigandine Ming):** couraça de tecido com pinos de rebite aparentes, elmo com
  aba, guardas de braço e caneleiras de ferro.

---

## Como usar

### Visualizador interativo (navegador)
Sirva a pasta `export/` e abra o `index.html`:
```bash
cd armor_r6/export
python3 -m http.server 8080 --bind 0.0.0.0
# abra http://localhost:8080/
```
O visualizador mostra **turntable 360° + animações Idle/Walk** das 4 variantes
(quadros renderizados pelo motor próprio, com a animação real aplicada ao rig).

### Gerar tudo (opcional — já vem pronto em `export/`)
```bash
cd armor_r6
python3 build.py          # ~40s, sem dependências
python3 make_viewer.py    # gera os quadros do visualizador (~4 min)
python3 validate.py       # verifica glb/bvh/obj
```

### Arquivos gerados em `export/`

```
export/
├── obj/            ← modelagem (Blender/Roblox)
│   ├── r6_mannequin.obj         manequim R6 (referência)
│   ├── european.obj             armadura em espaço-mundo (abrir no Blender)
│   ├── european_roblox_baked.obj  MESMA armadura "baked" no espaço local de cada parte
│   ├── (japanese / persian / ming …)  idem
│   └── armor.mtl                materiais
├── gltf/           ← rig + animação (Blender, Cascadeur, Roblox via importer)
│   ├── european.glb  (e japanese.glb, persian.glb, ming.glb)
├── bvh/            ← animação pura (Cascadeur)
│   ├── r6_idle.bvh, r6_walk.bvh, r6_run.bvh
├── lua/            ← Roblox Studio
│   ├── install_european.luau (e japanese/persian/ming)  solda das peças no rig
│   └── animations.luau   KeyframeSequences (idle/walk/run)
└── previews/       ← imagens PNG (frente / lateral / 3/4 / grade comparativa)
```

### No Roblox Studio (caminho recomendado)
1. Importe `obj/european_roblox_baked.obj` (File → Import 3D). Renomeie o Model para `Armor`.
2. Coloque `lua/install_european.luau` como **Script dentro** do model `Armor`,
   ajuste `CHARACTER_NAME` e rode — ele solda cada peça no lugar certo do R6 (C0/C1 = identidade,
   pois a geometria já vem no espaço local de cada parte).
3. Para animar, rode `lua/animations.luau` (cria e toca as animações Idle/Walk/Run).
4. Alternativa avançada: importe `gltf/european.glb` — já vem com esqueleto R6 +
   skinning + 3 animações.

### No Blender (quando disponível)
- `gltf/european.glb`: armadura + esqueleto R6 + animações (File → Import → glTF 2.0).
- `obj/european.obj` + `obj/r6_mannequin.obj`: geometria pura.
- `bvh/*.bvh`: animações para retarget.

### No Cascadeur (quando disponível)
- Importe `bvh/r6_walk.bvh` para o ciclo de caminhada pronto (o BVH já contém o
  deslocamento vertical do centro de massa, a assinatura do Cascadeur).

---

## Medidas usadas (rig R6 oficial, em studs)

| Parte | Center (x,y,z) | Size (x,y,z) |
|---|---|---|
| Torso | (0, 2.0, 0) | (2, 2, 1) |
| Head | (0, 3.6, 0) | (1.2, 1.2, 1.2) |
| Braço D | (1.5, 2.0, 0) | (1, 2, 1) |
| Braço E | (−1.5, 2.0, 0) | (1, 2, 1) |
| Perna D | (0.5, 1.0, 0) | (1, 2, 1) |
| Perna E | (−0.5, 1.0, 0) | (1, 2, 1) |

Convenções: **Y = para cima**, **+Z = frente**, **+X = direita** (igual ao Roblox e ao glTF).

Juntas do R6 (Motor6D): `Root Hip` (Torso), `Neck` (Head), `Right/Left Shoulder`
(braços), `Right/Left Hip` (pernas) — mapeadas automaticamente nos arquivos Lua/glb.

---

## Complexidade (triângulos por variante)

| Variante | Peças | Triângulos |
|---|---|---|
| european | 41 | ~11 144 |
| japanese | 45 | ~10 776 |
| persian | 26 | ~3 868 |
| ming | 23 | ~4 444 |

Para reduzir (limites de acessório no Roblox), diminua os parâmetros `segments=` nas
funções `tube`/`lathe`/`dome` em `engine/armor_models.py` e rode `build.py` de novo.

---

## Estrutura do código

```
armor_r6/
├── build.py               orquestrador (gera tudo)
├── make_viewer.py         quadros do visualizador + index.html
├── validate.py            verificação de integridade
├── PESQUISA_ARMADURAS.md  pesquisa histórica + fontes
├── engine/
│   ├── math3d.py          vetores, matrizes, quatérnios
│   ├── mesh.py            primitivas + espessamento + OBJ/MTL
│   ├── armor_models.py    as 4 armaduras históricas
│   ├── rig.py             esqueleto R6 + skinning
│   ├── animation.py       animações (idle/walk/run) + BVH + Lua
│   ├── gltf.py            exportador glTF 2.0 (.glb) com skin+animação
│   └── render.py          rasterizador de preview (PNG)
└── export/                artefatos prontos
```
