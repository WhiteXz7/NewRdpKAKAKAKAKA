"""math3d.py — Mini-biblioteca de matemática 3D (sem dependências externas).

Convenção global do projeto:
  * Eixo Y = para cima, +Z = frente, +X = direita do personagem (igual ao Roblox).
  * Matrizes 3x3 em listas de linhas: M = [[r0],[r1],[r2]]  ->  v' = M * v (coluna).
"""

import math

# ------------------------------------------------------------------------------
# Vetores (usamos tuplas/listas simples)
# ------------------------------------------------------------------------------

def vadd(a, b):        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vsub(a, b):        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vmul(a, s):        return (a[0] * s, a[1] * s, a[2] * s)
def vdiv(a, s):        return (a[0] / s, a[1] / s, a[2] / s)
def vneg(a):           return (-a[0], -a[1], -a[2])
def vdot(a, b):        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])
def vlen(a):           return math.sqrt(vdot(a, a))
def vnorm(a):
    l = vlen(a)
    if l < 1e-12:
        return (0.0, 0.0, 0.0)
    return (a[0] / l, a[1] / l, a[2] / l)
def vlerp(a, b, t):    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)

def clamp(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)

def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def ease_in_out(t):
    """Ease suave estilo 'Cascadeur' (aceleração/desaceleração natural)."""
    t = clamp(t, 0.0, 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)

# ------------------------------------------------------------------------------
# Matrizes de rotação 3x3 (v' = M * v, vetor coluna)
# ------------------------------------------------------------------------------

def mat_ident():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

def mat_rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]

def mat_rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]

def mat_rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]

def mat_mul(a, b):
    """a * b (ambas 3x3, listas de linhas)."""
    r = [[0.0, 0.0, 0.0] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            r[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]
    return r

def mat_vec(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])

def mat_transpose(m):
    return [[m[0][0], m[1][0], m[2][0]],
            [m[0][1], m[1][1], m[2][1]],
            [m[0][2], m[1][2], m[2][2]]]

def euler_xyz(rx, ry, rz):
    """Matriz de rotação a partir de ângulos de Euler (ordem X, depois Y, depois Z)."""
    return mat_mul(mat_mul(mat_rot_z(rz), mat_rot_y(ry)), mat_rot_x(rx))

def rot_about(pivot, m, p):
    """Aplica rotação m ao ponto p ao redor de 'pivot'."""
    d = vsub(p, pivot)
    return vadd(pivot, mat_vec(m, d))
