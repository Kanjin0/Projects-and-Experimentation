import pygame
from engine_config import *
from math_utils import Point2D, triangulate_polygon
from math import sqrt

#Draw rectangle with center at an x,y coord accounting for its size (so it's correctly placed there instead of placing the top right corner there) 
def point(point:Point2D):
    size = 10
    pygame.draw.rect(window, VERTEX_COLOR,(point.x - size/2, point.y- size/2,size,size))

#Draw a line conecting both points specified
def line(point1:Point2D, point2:Point2D):
    size = 2
    if DRAW_FACES: size = 5
    pygame.draw.line(window,EDGE_COLOR, (point1.x, point1.y), (point2.x, point2.y),size) 

#Draw a face of the model conecting all points specified
def face(points:list):
    pygame.draw.polygon(window,FACE_COLOR,points)


#Build a list of tuples representing edges from pre-defined faces
def build_wireframe_from_faces(faces:list):
    edges = set()
    for face in faces:
        for i in range(len(face)):
            v1 = face[i]
            v2 = face[(i+1) % len(face)]

            edge = tuple(sorted((v1,v2)))
            edges.add(edge)
    return list(edges)

def rasterize_triangle(p0, p1, p2, z0, z1, z2, color, pixels):
    """
    Barycentric rasterization with flat Z‑buffer and PixelArray.
    """
    W = Z_WIDTH
    H = Z_HEIGHT

    # Bounding box with sub‑pixel precision
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))

    if min_x > max_x or min_y > max_y:
        return

    # Pre‑compute edge vectors and denominator
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:  # Degenerate triangle
        return

    inv_denom = 1.0 / denom
    zb = Z_BUFFER

    for y in range(min_y, max_y + 1):
        row_offset = y * W
        for x in range(min_x, max_x + 1):
            # Compute barycentric coordinates
            v2x, v2y = x - p0.x, y - p0.y
            u = (v2x * v1y - v1x * v2y) * inv_denom
            v = (v0x * v2y - v2x * v0y) * inv_denom
            w = 1.0 - u - v

            # Inside test with epsilon
            if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                # Clamp to avoid negative values
                if u < 0: u = 0
                if v < 0: v = 0
                if w < 0: w = 0

                depth = u * z0 + v * z1 + w * z2
                idx = row_offset + x
                if depth < zb[idx]:
                    zb[idx] = depth
                    pixels[x, y] = color   # fast pixel access

def rasterize_triangle_tiled(p0, p1, p2, z0, z1, z2, color, pixels):
    """
    Tile‑based (8x8) barycentric rasterizer with flat Z‑buffer and PixelArray.
    """
    TILE = 32
    W = Z_WIDTH
    H = Z_HEIGHT

    # Bounding box (clamped to screen)
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))
    if min_x > max_x or min_y > max_y:
        return

    # Pre‑compute barycentric constants
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:
        return
    inv_denom = 1.0 / denom

    # Tile range (inclusive)
    tx_start = min_x // TILE
    tx_end = max_x // TILE
    ty_start = min_y // TILE
    ty_end = max_y // TILE

    zb = Z_BUFFER

    for ty in range(ty_start, ty_end + 1):
        tile_y = ty * TILE
        for tx in range(tx_start, tx_end + 1):
            tile_x = tx * TILE

            # Quick reject: if tile is entirely outside the triangle's bounding box
            if tile_x > max_x or tile_x + TILE - 1 < min_x:
                continue
            if tile_y > max_y or tile_y + TILE - 1 < min_y:
                continue

            # Process the 8x8 tile
            for dy in range(TILE):
                y = tile_y + dy
                if y > max_y:
                    break
                row_offset = y * W
                for dx in range(TILE):
                    x = tile_x + dx
                    if x > max_x:
                        break

                    # Barycentric inside test
                    v2x, v2y = x - p0.x, y - p0.y
                    u = (v2x * v1y - v1x * v2y) * inv_denom
                    v = (v0x * v2y - v2x * v0y) * inv_denom
                    w = 1.0 - u - v

                    if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                        # Clamp to avoid negative values
                        if u < 0: u = 0
                        if v < 0: v = 0
                        if w < 0: w = 0

                        depth = u * z0 + v * z1 + w * z2
                        idx = row_offset + x
                        if depth < zb[idx]:
                            zb[idx] = depth
                            pixels[x, y] = color   # faster pixel access


def rasterize_triangle_tiled_lighting(p0, p1, p2, z0, z1, z2, pixels,
                                      color0=None, color1=None, color2=None,
                                      n0=None, n1=None, n2=None,
                                      base_color=None):
    TILE = 8
    W = Z_WIDTH
    H = Z_HEIGHT
    mode = SHADING_MODE

    # ---- Bounding Box ----
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(W - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(H - 1, max(p0.y, p1.y, p2.y)))
    if min_x > max_x or min_y > max_y:
        return

    # ---- Barycentric Setup ----
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

    # ---- Light Setup ----
    ambient = AMBIENT_STRENGTH
    ldx, ldy, ldz = LIGHT_DIR
    l_len = sqrt(ldx*ldx + ldy*ldy + ldz*ldz)
    if l_len > 1e-10:
        ldx /= l_len; ldy /= l_len; ldz /= l_len
    spec_strength = SPECULAR_STRENGTH
    shininess = SHININESS
    vx, vy, vz = 0.0, 0.0, 1.0  # view direction (simplified)

    # ---- Initialize all variables to avoid "unbound" warnings ----
    r_base = g_base = b_base = 0
    r0 = g0 = b0 = 0
    r1 = g1 = b1 = 0
    r2 = g2 = b2 = 0
    use_flat = True  # default: fallback to flat color

    # ---- Pre‑compute per‑mode constants ----
    if mode == SHADING_NONE:
        r_base, g_base, b_base = base_color

    elif mode == SHADING_GOURAUD:
        # If any vertex color is missing, fall back to flat color
        if color0 is None or color1 is None or color2 is None:
            r0, g0, b0 = base_color
            r1, g1, b1 = base_color
            r2, g2, b2 = base_color
        else:
            r0, g0, b0 = color0
            r1, g1, b1 = color1
            r2, g2, b2 = color2

    else:  # PHONG
        if n0 is None or n1 is None or n2 is None:
            use_flat = True
        else:
            use_flat = False

    # ---- Tile & Pixel Loops ----
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

                    # Barycentric weights
                    v2x, v2y = x - p0.x, y - p0.y
                    u = (v2x * v1y - v1x * v2y) * inv_denom
                    v = (v0x * v2y - v2x * v0y) * inv_denom
                    w = 1.0 - u - v

                    if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                        if u < 0: u = 0
                        if v < 0: v = 0
                        if w < 0: w = 0

                        # Interpolate depth
                        depth = u * z0 + v * z1 + w * z2
                        idx = row_offset + x
                        if depth < zb[idx]:
                            zb[idx] = depth

                            # ---- Shading Dispatch ----
                            if mode == SHADING_NONE:
                                pixels[x, y] = (r_base, g_base, b_base)

                            elif mode == SHADING_GOURAUD:
                                # Interpolate vertex colors
                                r = int(u * r0 + v * r1 + w * r2)
                                g = int(u * g0 + v * g1 + w * g2)
                                b = int(u * b0 + v * b1 + w * b2)
                                pixels[x, y] = (min(255, max(0, r)),
                                                min(255, max(0, g)),
                                                min(255, max(0, b)))

                            else:  # PHONG
                                if use_flat:
                                    pixels[x, y] = base_color
                                else:
                                    # Interpolate normal (now guaranteed not None)
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

def compute_vertex_color(normal, base_color, ambient, light_dir, spec_strength, shininess, view_dir=(0,0,1)):
    """
    Compute the shaded color for a single vertex.
    Returns (r, g, b) as ints (0-255).
    """
    ldx, ldy, ldz = light_dir
    vx, vy, vz = view_dir

    # Diffuse
    diff = max(0.0, normal.x * ldx + normal.y * ldy + normal.z * ldz)
    intensity = ambient + (1.0 - ambient) * diff

    # Specular (Blinn-Phong)
    hx = ldx + vx
    hy = ldy + vy
    hz = ldz + vz
    h_len = sqrt(hx*hx + hy*hy + hz*hz)
    if h_len > 1e-10:
        hx /= h_len; hy /= h_len; hz /= h_len
        spec = pow(max(0.0, normal.x*hx + normal.y*hy + normal.z*hz), shininess)
        intensity += spec_strength * spec

    if intensity > 1.0:
        intensity = 1.0

    r = int(base_color[0] * intensity)
    g = int(base_color[1] * intensity)
    b = int(base_color[2] * intensity)
    return (r, g, b)