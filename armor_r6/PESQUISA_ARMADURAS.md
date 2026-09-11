# PESQUISA — Armaduras Históricas Reais (para o rig R6 do Roblox)

> Documento de referência usado para modelar a armadura de ferro **completa** (Europeia) e suas
> variações pelo mundo. Cada peça do modelo 3D corresponde a uma peça histórica real, listada aqui.

---

## 1. Armadura de Placas Completa Europeia (séc. XV, c. 1420–1500)

A "armadura de ferro completa" que existiu na vida real é a **armadura de placas completa**
(*full plate armour / harness*), usada sobretudo por cavaleiros e homens de armas na Europa
Ocidental (Itália — estilo **Milanês**; Alemanha — estilo **Gótico**; e Inglaterra/França).
Ela era vestida por cima de um **gambeson/arming doublet** (acolchoado) e de **cota de malha**
nas juntas (axilas, cotovelos, virilha).

### Peças que compõem a armadura completa (de cima para baixo)

| # | Peça (nome real) | Função / local | No modelo |
|---|---|---|---|
| 1 | **Helmo / Elmo** (armet, close helmet, sallet, bascinet+visor) | Crânio e rosto | `helmet` |
| 2 | **Gorget** (gorgeira / colarinho) e **bevor** (barbote) | Pescoço e garganta | `gorget` |
| 3 | **Pauldron** (ombreira) + **besagew/rondel** (disco da axila) | Ombro e axila | `pauldron_L/R`, `rondel_L/R` |
| 4 | **Rerebrace** (braçal superior) | Bíceps | `rerebrace_L/R` |
| 5 | **Couter** (codo/cotoveleira) | Cotovelo | `couter_L/R` |
| 6 | **Vambrace** (antebraçal) | Antebraço | `vambrace_L/R` |
| 7 | **Gauntlet** (manopla) | Mão | `gauntlet_L/R` |
| 8 | **Cuirass** = **Breastplate** (peitoral) + **Backplate** (dorsal) | Tronco | `cuirass_front`, `cuirass_back` |
| 9 | **Fauld** (fraldão de lâminas) | Cintura/quadril | `fauld_lame_1..3` |
| 10 | **Tasset** (coxote articulado) + **culet** (rabadilha) | Coxa dianteira/traseira | `tasset_L/R`, `culet` |
| 11 | **Cuisse** (coxal) | Coxa | `cuisse_L/R` |
| 12 | **Poleyn** (joelheira) | Joelho | `poleyn_L/R` |
| 13 | **Greave** (caneleira) | Canela/panturrilha | `greave_L/R` |
| 14 | **Sabaton** (escarpim/peúga de aço) | Pé | `sabaton_L/R` |

**Detalhes históricos aplicados ao modelo:**
- **Fluting / caneluras** (reforço em "vincos" no peitoral e ombreiras) — típicas do estilo Gótico.
- **Lâminas articuladas (lames)** sobrepostas no fauld, tasset, ombreiras — permitiam movimento.
- **Rondéis (besagews)** protegendo as axilas.
- **Manopla de "mitten"** (dedos juntos, não dedos separados).
- **Garnitures / peças de troca**: os elmos e armaduras de luxo tinham peças intercambiáveis
  (para torneio vs. guerra) — no modelo, o elmo e as variações de ombreira podem ser trocados.

---

## 2. Variações pelo mundo (referências históricas)

### 2.1 Japão — ō-yoroi e tōsei-gusoku (samurai)
- **Ō-yoroi** ("grande armadura", períodos Heian–Kamakura): armadura **lamelar** (escamas
  *kozane* lacadas e atadas com cordões de seda coloridos), feita para **arqueiros montados**.
  Caixa rígida no tronco, com grandes ombreiras **ō-sode** que serviam de escudo.
- **Tōsei-gusoku** (era Sengoku): armadura "moderna" do samurai.
- Peças: **kabuto** (elmo com *shikoro* na nuca e *maedate*), **menpō** (máscara facial),
  **dō** (couraça do tronco), **kusazuri** (saia de lâminas no quadril), **sode** (ombreiras
  retangulares), **kote** (mangas), **haidate** (coxais), **suneate** (caneleiras), **nodowa**
  (gola), **kōgake** (sapatos). Contato com os portugueses no séc. XVI trouxe couraças
  europeias ("nanban") para o Japão.

### 2.2 Pérsia / Índia / Otomanos — chahar-aina ("quatro espelhos")
- **Chahar-aina / char-aina** ("quatro espelhos"): **4 placas de metal** (peito, costas e 2
  laterais) usadas por cima de uma **cota de malha (zirah)**. Surgiu na Pérsia no séc. XV e se
  espalhou pela Índia Mogol e pelo Império Otomano. Placas do peito/costas maiores, laterais com
  reentrância para os braços. Leve e muito móvel.
- **Kulah khud / khula-khud**: elmo semiesférico com **espigão no topo**, **nasal** e
  **avental de malha** descendo pela nuca.
- **Dastana / bazu-band**: protetores de braço com guarda-mão.
- **Zirah pajama**: calças de malha. **Dhal**: escudo redondo.
- Otomanos também usavam **mirror armour / krug** e elmos tipo **chichak**.

### 2.3 China — brigandine Ming e "armadura padrão-montanha"
- **Brigandine (bǎijiǎ / dīngjiǎ, 布面甲)**: placas de ferro **rebitadas por dentro** de tecido
  (seda/couro), com as cabeças dos rebites visíveis do lado de fora. Foi a armadura dominante da
  **dinastia Ming** e continuou na Qing (virando cerimonial). Muito usada por infantaria.
- **Lamellar** (lâminas lacadas sobrepostas): padrão chinês desde os Estados Combatentes.
- **Shan wen kai (山文甲, "armadura padrão-montanha")**: padrão de lâminas intertravadas em
  losangos/hexágonos, retratado em estátuas e pinturas Tang–Ming. Não sobreviveu nenhum original
  e sua construção real ainda é debatida (pode ser representação artística de malha).

### 2.4 Outras
- **Mongóis (séc. XIII, Império Mongol/Yuan)**: **armadura lamelar** (lâminas de ferro/couro
  atadas em fileiras sobrepostas), leve para a cavalaria; elmo cônico **duulga** com protetor
  de nuca lamelar e aro de pele; couraça e mangas flexíveis.
- **Coreia (dinastia Joseon, séc. XIV–XIX)**: armadura **lamelar/brigandine** lacada
  (vermelho/ferro), elmo com **aba larga** e espigão; semelhante à chinesa mas com silhueta
  e elmo próprios.
- **África**: clima quente → pouca armadura de metal; ênfase em **escudos** grandes.
- **Ásia Central/estepes**: lamellar de couro/ferro, comum entre turcos, cazares e mongóis.

---

## 3. O rig R6 do Roblox (referência técnica)

O **R6** é o corpo clássico de **6 partes** (Cabeça, Torso, 2 Braços, 2 Pernas). Medidas oficiais
(Roblox Creator Docs — "Classic body scale", em studs; 1 stud ≈ 28 cm):

| Parte | Largura (X) | Altura (Y) | Profundidade (Z) |
|---|---|---|---|
| Head | 1.5 | 1.8 | 2 |
| Torso | 4 | 3.8 | 2 |
| Arm (cada) | 2 | 3 | 2 |
| Leg (cada) | 1.5 | 3.5 | 2 |

**Proporção usada neste projeto (rig R6 padrão de "junta de esfera", Y = para cima):**

| Parte | Center (x, y, z) | Size (x, y, z) | Alcance |
|---|---|---|---|
| Torso | (0, 2.0, 0) | (2, 2, 1) | x: −1..1, y: 1..3 |
| Head | (0, 3.6, 0) | (1.2, 1.2, 1.2) | y: 3.0..4.2 |
| Braço Direito | (1.5, 2.0, 0) | (1, 2, 1) | x: 1..2, y: 1..3 |
| Braço Esquerdo | (−1.5, 2.0, 0) | (1, 2, 1) | x: −2..−1 |
| Perna Direita | (0.5, 1.0, 0) | (1, 2, 1) | x: 0..1, y: 0..2 |
| Perna Esquerda | (−0.5, 1.0, 0) | (1, 2, 1) | x: −1..0 |

> Convenções do modelo: **eixo Y = para cima**, **+Z = frente** (para onde o visor aponta),
> **+X = direita do personagem**. O arquivo `.obj` usa Y-up, igual ao Roblox e ao Cascadeur.
> Todas as peças são modeladas **com folga (clearance)** de ~0,06–0,12 stud sobre o corpo,
> para encaixarem sobre o rig sem cortar (clipping) o bloco do R6.

**Como as peças encaixam no rig (mapeamento para solda no Studio):**

| Peça da armadura | Parte do R6 (pai / weld) |
|---|---|
| helmet, kabuto, kulah_khud, menpo | Head |
| gorget, cuirass, fauld, tasset, culet, rondel, pauldron, sode | Torso |
| rerebrace, couter, vambrace, gauntlet | Braço esq./dir. |
| cuisse, poleyn, greave, sabaton, suneate | Perna esq./dir. |

---

## 4. Referências (fontes consultadas)

- Roblox Creator Docs — Character body specifications:
  https://create.roblox.com/docs/avatar/character-bodies/specifications
- Wikipedia — Plate armour: https://en.wikipedia.org/wiki/Plate_armour
- ArmStreet — Gothic Armour Kit (nomenclatura das peças): https://armstreet.com/store/armor/medieval-knight-gothic-plate-armour-kit
- Celtic Web Merchant — componentes de armadura de placas: https://www.celticwebmerchant.com/en-int/collections/plate-armor
- EverybodyWiki — Components of medieval armour (análogos japoneses): https://en.everybodywiki.com/Components_of_medieval_armour
- Katana Store — Samurai Armor: https://katana.store/blogs/katana-blog/samurai-armor
- Romance of Men — Ō-yoroi complete guide: https://romanceofmen.com/blogs/armor-knowledge/oyoroi-complete-guide-to-understand-the-japanese-great-armor
- Louvre Abu Dhabi — Mail and Plate Armour "Four Mirrors": https://collection.louvreabudhabi.ae/en/object/mail-and-plate-armour-called-four-mirrors-armour
- Oxford Pitt Rivers Museum — Chinese brigandine: https://web.prm.ox.ac.uk/weapons/index.php/tour-by-region/asia/asia/arms-and-armour-asia-74/index.html
- Great Ming Military — The myths of Shan Wen Kia: https://greatmingmilitary.blogspot.com/2015/08/myth-of-shan-wen-kia.html
