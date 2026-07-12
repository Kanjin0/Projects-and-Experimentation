import pygame
from engine_config import *
from math_utils import Point2D
from math import sqrt

# ---- Drawing functions (unchanged) ----
def point(point: Point2D):
    size = 10
    pygame.draw.rect(window, VERTEX_COLOR, (point.x - size/2, point.y - size/2, size, size))

def line(point1: Point2D, point2: Point2D):
    size = 2
    if DRAW_FACES:
        size = 5
    pygame.draw.line(window, EDGE_COLOR, (point1.x, point1.y), (point2.x, point2.y), size)

def face(points: list):
    pygame.draw.polygon(window, FACE_COLOR, points)

def build_wireframe_from_faces(faces: list):
    edges = set()
    for face in faces:
        for i in range(len(face)):
            v1 = face[i]
            v2 = face[(i + 1) % len(face)]
            edges.add(tuple(sorted((v1, v2))))
    return list(edges)

# ---- Rasterizers (flat and Phong) ----
def rasterize_triangle(p0, p1, p2, z0, z1, z2, color, pixels):
    W = Z_WIDTH
    H = Z_HEIGHT
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))
    if min_x > max_x or min_y > max_y:
        return
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:
        return
    inv_denom = 1.0 / denom
    zb = Z_BUFFER
    for y in range(min_y, max_y + 1):
        row_offset = y * W
        for x in range(min_x, max_x + 1):
            v2x, v2y = x - p0.x, y - p0.y
            u = (v2x * v1y - v1x * v2y) * inv_denom
            v = (v0x * v2y - v2x * v0y) * inv_denom
            w = 1.0 - u - v
            if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                if u < 0: u = 0
                if v < 0: v = 0
                if w < 0: w = 0
                depth = u * z0 + v * z1 + w * z2
                idx = row_offset + x
                if depth < zb[idx]:
                    zb[idx] = depth
                    pixels[x, y] = color

def rasterize_triangle_tiled(p0, p1, p2, z0, z1, z2, color, pixels):
    TILE = 32
    W = Z_WIDTH
    H = Z_HEIGHT
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))
    if min_x > max_x or min_y > max_y:
        return
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:
        return
    inv_denom = 1.0 / denom
    tx_start = min_x // TILE
    tx_end = max_x // TILE
    ty_start = min_y // TILE
    ty_end = max_y // TILE
    zb = Z_BUFFER
    for ty in range(ty_start, ty_end + 1):
        tile_y = ty * TILE
        for tx in range(tx_start, tx_end + 1):
            tile_x = tx * TILE
            if tile_x > max_x or tile_x + TILE - 1 < min_x:
                continue
            if tile_y > max_y or tile_y + TILE - 1 < min_y:
                continue
            for dy in range(TILE):
                y = tile_y + dy
                if y > max_y:
                    break
                row_offset = y * W
                for dx in range(TILE):
                    x = tile_x + dx
                    if x > max_x:
                        break
                    v2x, v2y = x - p0.x, y - p0.y
                    u = (v2x * v1y - v1x * v2y) * inv_denom
                    v = (v0x * v2y - v2x * v0y) * inv_denom
                    w = 1.0 - u - v
                    if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                        if u < 0: u = 0
                        if v < 0: v = 0
                        if w < 0: w = 0
                        depth = u * z0 + v * z1 + w * z2
                        idx = row_offset + x
                        if depth < zb[idx]:
                            zb[idx] = depth
                            pixels[x, y] = color

# ---- Lighting rasterizer (Flat or Phong) ----
def rasterize_triangle_tiled_lighting(p0, p1, p2, z0, z1, z2, pixels,
                                      n0=None, n1=None, n2=None,
                                      base_color=None):
    TILE = 32
    W = Z_WIDTH
    H = Z_HEIGHT
    mode = SHADING_MODE

    # ---- Bounding box ----
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))
    if min_x > max_x or min_y > max_y:
        return

    # ---- Barycentric setup ----
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:
        return
    inv_denom = 1.0 / denom

    tx_start = min_x // TILE
    tx_end = max_x // TILE
    ty_start = min_y // TILE
    ty_end = max_y // TILE

    zb = Z_BUFFER

    # ---- Initialise lighting variables to default (avoid unbound warnings) ----
    use_phong = False
    ambient = 0.0
    ldx = ldy = ldz = 0.0
    spec_strength = 0.0
    shininess = 1.0
    vx = vy = vz = 0.0

    # ---- Check if Phong mode is active and normals are provided ----
    if mode == SHADING_PHONG and n0 is not None and n1 is not None and n2 is not None:
        use_phong = True
        ambient = AMBIENT_STRENGTH
        ldx, ldy, ldz = LIGHT_DIR
        l_len = sqrt(ldx*ldx + ldy*ldy + ldz*ldz)
        if l_len > 1e-10:
            ldx /= l_len; ldy /= l_len; ldz /= l_len
        spec_strength = SPECULAR_STRENGTH
        shininess = SHININESS
        vx, vy, vz = 0.0, 0.0, 1.0   # view direction (simplified)

    # ---- Flat colour ----
    if base_color is None:
        base_color = FACE_COLOR
    r_base, g_base, b_base = base_color

    # ---- Tile loops ----
    for ty in range(ty_start, ty_end + 1):
        tile_y = ty * TILE
        for tx in range(tx_start, tx_end + 1):
            tile_x = tx * TILE
            if tile_x > max_x or tile_x + TILE - 1 < min_x:
                continue
            if tile_y > max_y or tile_y + TILE - 1 < min_y:
                continue

            for dy in range(TILE):
                y = tile_y + dy
                if y > max_y:
                    break
                row_offset = y * W
                for dx in range(TILE):
                    x = tile_x + dx
                    if x > max_x:
                        break

                    v2x, v2y = x - p0.x, y - p0.y
                    u = (v2x * v1y - v1x * v2y) * inv_denom
                    v = (v0x * v2y - v2x * v0y) * inv_denom
                    w = 1.0 - u - v

                    if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                        if u < 0: u = 0
                        if v < 0: v = 0
                        if w < 0: w = 0

                        depth = u * z0 + v * z1 + w * z2
                        idx = row_offset + x
                        if depth < zb[idx]:
                            zb[idx] = depth

                            if not use_phong:
                                # Flat shading
                                pixels[x, y] = (r_base, g_base, b_base)
                            else:
                                # ---- Phong shading ----
                                # Tell type checker these are guaranteed non‑None
                                assert n0 is not None and n1 is not None and n2 is not None

                                # Interpolate normal
                                nx = u * n0.x + v * n1.x + w * n2.x
                                ny = u * n0.y + v * n1.y + w * n2.y
                                nz = u * n0.z + v * n1.z + w * n2.z
                                n_len = sqrt(nx*nx + ny*ny + nz*nz)
                                if n_len > 1e-10:
                                    nx /= n_len; ny /= n_len; nz /= n_len
                                else:
                                    nx, ny, nz = 0, 1, 0

                                # Diffuse
                                diff = max(0.0, nx*ldx + ny*ldy + nz*ldz)
                                intensity = ambient + (1.0 - ambient) * diff

                                # Specular (Blinn-Phong)
                                hx = ldx + vx
                                hy = ldy + vy
                                hz = ldz + vz
                                h_len = sqrt(hx*hx + hy*hy + hz*hz)
                                if h_len > 1e-10:
                                    hx /= h_len; hy /= h_len; hz /= h_len
                                    spec = pow(max(0.0, nx*hx + ny*hy + nz*hz), shininess)
                                    intensity += spec_strength * spec

                                if intensity > 1.0:
                                    intensity = 1.0

                                r = int(base_color[0] * intensity)
                                g = int(base_color[1] * intensity)
                                b = int(base_color[2] * intensity)
                                pixels[x, y] = (min(255, r), min(255, g), min(255, b))