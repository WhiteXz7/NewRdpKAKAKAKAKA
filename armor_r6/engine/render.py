"""render.py — Rasterizador de software (substituto de viewport para preview).

Renderiza malhas trianguladas com sombreamento de Gouraud (luz difusa + ambiente),
z-buffer e câmera em perspectiva. Salva PNG via zlib (stdlib).
"""

import math
import struct
import zlib

from . import math3d as m3
from .mesh import compute_normals


def _write_png(path, w, h, rgb):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        return c

    raw = b"".join(b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


class Camera:
    def __init__(self, eye, target, up=(0, 1, 0), fov=40.0):
        self.eye = tuple(eye)
        self.target = tuple(target)
        self.up = tuple(up)
        self.fov = math.radians(fov)
        self._basis()

    def _basis(self):
        fwd = m3.vnorm(m3.vsub(self.target, self.eye))
        right = m3.vnorm(m3.vcross(fwd, self.up))
        up = m3.vcross(right, fwd)
        self._fwd = fwd
        self._right = right
        self._up = up

    def to_cam(self, p):
        d = m3.vsub(p, self.eye)
        return (m3.vdot(d, self._right), m3.vdot(d, self._up), m3.vdot(d, self._fwd))


class Renderer:
    def __init__(self, w, h, bg=(30, 34, 42)):
        self.w, self.h = w, h
        self.bg = bg
        self.clear()

    def clear(self):
        self.depth = [1e18] * (self.w * self.h)
        self.color = [self.bg] * (self.w * self.h)

    def set_viewport(self, x0, y0, x1, y1):
        self.vp = (x0, y0, x1, y1)

    def project(self, cam, p):
        c = cam.to_cam(p)
        if c[2] < 0.05:
            return None
        vx0, vy0, vx1, vy1 = getattr(self, "vp", (0, 0, self.w, self.h))
        vw, vh = vx1 - vx0, vy1 - vy0
        f = (vh / 2.0) / math.tan(cam.fov / 2.0)
        x = vx0 + vw / 2.0 + c[0] * f / c[2]
        y = vy0 + vh / 2.0 - c[1] * f / c[2]
        return (x, y, c[2])

    def draw_mesh(self, cam, mesh, base_color, light_dir, ambient=0.45):
        tris = mesh.faces
        verts = mesh.verts
        normals = compute_normals(mesh)
        ldir = m3.vnorm(light_dir)

        # cor base do material
        r0, g0, b0 = base_color

        # pré-projeta
        proj = [self.project(cam, v) for v in verts]
        norm_cam = [cam.to_cam(v) for v in verts]

        for f in tris:
            if len(f) != 3:
                continue
            p = [proj[f[0]], proj[f[1]], proj[f[2]]]
            if any(q is None for q in p):
                continue
            # sombreamento por vértice (Gouraud)
            shade = []
            for i in (0, 1, 2):
                n = normals[f[i]]
                nd = m3.vdot(n, ldir)
                lam = ambient + (1.0 - ambient) * max(0.0, nd)
                shade.append(lam)
            ax, ay = p[0][0], p[0][1]
            bx, by = p[1][0], p[1][1]
            cx, cy = p[2][0], p[2][1]
            area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if abs(area) < 1e-9:
                continue
            # normaliza o winding para area positiva (tela y para baixo)
            if area < 0:
                p[1], p[2] = p[2], p[1]
                shade[1], shade[2] = shade[2], shade[1]
                ax, ay = p[0][0], p[0][1]
                bx, by = p[1][0], p[1][1]
                cx, cy = p[2][0], p[2][1]
                area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

            vx0, vy0, vx1, vy1 = getattr(self, "vp", (0, 0, self.w, self.h))
            xmin = max(vx0, int(min(p[0][0], p[1][0], p[2][0])))
            xmax = min(vx1 - 1, int(max(p[0][0], p[1][0], p[2][0])))
            ymin = max(vy0, int(min(p[0][1], p[1][1], p[2][1])))
            ymax = min(vy1 - 1, int(max(p[0][1], p[1][1], p[2][1])))

            for y in range(ymin, ymax + 1):
                for x in range(xmin, xmax + 1):
                    px, py = x + 0.5, y + 0.5
                    w0 = (by - cy) * (px - cx) + (cx - bx) * (py - cy)
                    w1 = (cy - ay) * (px - cx) + (ax - cx) * (py - cy)
                    w2 = area - w0 - w1
                    if w0 < 0 or w1 < 0 or w2 < 0:
                        continue
                    w0 /= area; w1 /= area; w2 /= area
                    z = w0 * p[0][2] + w1 * p[1][2] + w2 * p[2][2]
                    idx = y * self.w + x
                    if z >= self.depth[idx]:
                        continue
                    self.depth[idx] = z
                    s = w0 * shade[0] + w1 * shade[1] + w2 * shade[2]
                    col = (int(r0 * s), int(g0 * s), int(b0 * s))
                    self.color[idx] = col

    def save_png(self, path):
        rgb = bytearray(self.w * self.h * 3)
        for i, c in enumerate(self.color):
            rgb[i * 3] = min(255, c[0])
            rgb[i * 3 + 1] = min(255, c[1])
            rgb[i * 3 + 2] = min(255, c[2])
        _write_png(path, self.w, self.h, rgb)


def render_scene(meshes_with_color, camera, size=(480, 640), light_dir=(0.5, 0.8, 0.6)):
    """Renderiza uma lista de (mesh, (r,g,b)) com uma câmera dada. Retorna Renderer."""
    r = Renderer(size[0], size[1])
    for mesh, col in meshes_with_color:
        r.draw_mesh(camera, mesh, col, light_dir)
    return r
