import pygame
from engine_config import Z_BUFFER, VERTEX_COLOR,EDGE_COLOR, FACE_COLOR, DRAW_FACES, window, window_height, window_width
from math_utils import Point2D, triangulate_polygon

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

def rasterize_triangle(p0, p1, p2, z0, z1, z2, color):
    """
    Barycentric rasterization with proper epsilon handling.
    """
    # Bounding box with sub‑pixel precision
    min_x = int(max(0, min(p0.x, p1.x, p2.x)))
    max_x = int(min(window_width - 1, max(p0.x, p1.x, p2.x)))
    min_y = int(max(0, min(p0.y, p1.y, p2.y)))
    max_y = int(min(window_height - 1, max(p0.y, p1.y, p2.y)))

    if min_x > max_x or min_y > max_y:
        return

    # Pre‑compute edge vectors and denominator
    v0x, v0y = p1.x - p0.x, p1.y - p0.y
    v1x, v1y = p2.x - p0.x, p2.y - p0.y
    denom = v0x * v1y - v1x * v0y
    if abs(denom) < 1e-10:  # Degenerate triangle
        return

    # Pre‑compute inverse denominator
    inv_denom = 1.0 / denom

    zb =  Z_BUFFER

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            # Compute barycentric coordinates
            v2x, v2y = x - p0.x, y - p0.y
            u = (v2x * v1y - v1x * v2y) * inv_denom
            v = (v0x * v2y - v2x * v0y) * inv_denom
            w = 1.0 - u - v

            # Inside test with epsilon to catch edge pixels
            if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                # Clamp to avoid negative values (due to floating point)
                if u < 0: u = 0
                if v < 0: v = 0
                if w < 0: w = 0

                # Interpolate depth (perspective‑correct would be better, but this is fine)
                depth = u * z0 + v * z1 + w * z2

                if depth < zb[y][x]:
                    zb[y][x] = depth
                    window.set_at((x, y), color)

def rasterize_triangle_tiled(p0, p1, p2, z0, z1, z2, color):
    """
    Tile‑based (8x8) barycentric rasterizer with Z‑buffer.
    """
    TILE = 32
    W = window_width
    H = window_height

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
                        if depth < zb[y][x]:
                            zb[y][x] = depth
                            window.set_at((x, y), color)