from typing import NamedTuple
from engine_config import window_height, window_width
from math import cos, sin, sqrt

class Point2D(NamedTuple):
    x: float
    y: float

class Point3D(NamedTuple):
    x: float
    y: float
    z: float

#Calculate the direction the normal of the face belonging to the plane defined by the 3 parameter points is facing
#Deprecated, was used during the loop but now is substituted by the one below
def calculate_face_normal(p0:Point3D,p1:Point3D,p2:Point3D):

    #Direction vectors
    v0 = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
    v1 = (p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)

    #Cross Product
    a = v0[1]*v1[2] - v0[2]*v1[1]
    b = v0[2]*v1[0] - v0[0]*v1[2]
    c = v0[0]*v1[1] - v0[1]*v1[0]

    return (a,b,c)

#Used to pre-compute the normals of all faces before the loop so we'll have higher performance in more detailed models
def compute_face_normals(vertices: list[Point3D], faces:list[list[int]]) -> list[tuple[float, float, float]]:
    normals = [] 

    for face in faces:
        p0,p1,p2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

        v0 = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
        v1 = (p2.x - p0.x, p2.y - p0.y, p2.z - p0.z)

        nx = v0[1] * v1[2] - v0[2] * v1[1]
        ny = v0[2] * v1[0] - v0[0] * v1[2]
        nz = v0[0] * v1[1] - v0[1] * v1[0]

         # Normalize
        length = sqrt(nx*nx + ny*ny + nz*nz)
        if length > 1e-10:
            nx /= length; ny /= length; nz /= length
        else:
            nx = ny = nz = 0.0   # fallback (shouldn't happen for valid geometry)

        normals.append((nx, ny, nz))

    return normals

#Triangulates a polygon (convex or concave) using the ear clipping algorithm. Returns a list of triangles, each as a tuple of indices into the original points list.
def triangulate_polygon(points: list[Point2D]) -> list[tuple[int, int, int]]:
    n = len(points)
    if n < 3:
        return []
    if n == 3:
        return [(0, 1, 2)]

    # Helper: check if vertex i is convex
    def is_convex(i):
        p0 = points[(i - 1) % n]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        cross = (p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x)
        if polygon_is_ccw:
            return cross > 0
        else:
            return cross < 0

    # Determine if the polygon is counter‑clockwise
    area = 0.0
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        area += p1.x * p2.y - p2.x * p1.y
    polygon_is_ccw = area > 0

    # Helper: check if point p is inside triangle (a, b, c)
    def point_in_triangle(p, a, b, c):
        v0 = (c.x - a.x, c.y - a.y)
        v1 = (b.x - a.x, b.y - a.y)
        v2 = (p.x - a.x, p.y - a.y)

        dot00 = v0[0]*v0[0] + v0[1]*v0[1]
        dot01 = v0[0]*v1[0] + v0[1]*v1[1]
        dot02 = v0[0]*v2[0] + v0[1]*v2[1]
        dot11 = v1[0]*v1[0] + v1[1]*v1[1]
        dot12 = v1[0]*v2[0] + v1[1]*v2[1]

        denom = dot00 * dot11 - dot01 * dot01
        if abs(denom) < 1e-10:
            return False
        inv_denom = 1.0 / denom
        u = (dot11 * dot02 - dot01 * dot12) * inv_denom
        v = (dot00 * dot12 - dot01 * dot02) * inv_denom
        return (u >= 0) and (v >= 0) and (u + v <= 1)

    # Ear clipping
    triangles = []
    remaining = list(range(n))
    while len(remaining) > 3:
        ear_found = False
        for i in range(len(remaining)):
            prev = remaining[(i - 1) % len(remaining)]
            curr = remaining[i]
            next_idx = remaining[(i + 1) % len(remaining)]

            if not is_convex(curr):
                continue

            p_prev = points[prev]
            p_curr = points[curr]
            p_next = points[next_idx]

            contains_point = False
            for j in remaining:
                if j == prev or j == curr or j == next_idx:
                    continue
                if point_in_triangle(points[j], p_prev, p_curr, p_next):
                    contains_point = True
                    break
            if not contains_point:
                triangles.append((prev, curr, next_idx))
                remaining.pop(i)
                ear_found = True
                break
        if not ear_found:
            # Fallback: if no ear found, polygon may be degenerate or self-intersecting
            break

    if len(remaining) == 3:
        triangles.append((remaining[0], remaining[1], remaining[2]))
    return triangles

#Triangulates a single face using the original 3D vertices. Returns a list of (i, j, k) triangles (indices into the original vertices list).
def triangulate_face(vertices_3d: list[Point3D], face_indices: list[int]) -> list[tuple[int, int, int]]:
    if len(face_indices) < 3:
        return []
    if len(face_indices) == 3:
        return [(face_indices[0], face_indices[1], face_indices[2])]

    # Get the 3D points for this face
    pts_3d = [vertices_3d[i] for i in face_indices]

    # Find a plane to project the 3D points to 2D for ear clipping
    # Use the first three points to define the plane
    p0 = pts_3d[0]
    p1 = pts_3d[1]
    p2 = pts_3d[2]

    # Compute normal of the face plane
    v0 = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
    v1 = (p2.x - p0.x, p2.y - p0.y, p2.z - p0.z)
    nx = v0[1] * v1[2] - v0[2] * v1[1]
    ny = v0[2] * v1[0] - v0[0] * v1[2]
    nz = v0[0] * v1[1] - v0[1] * v1[0]
    normal = (nx, ny, nz)

    # Compute two orthonormal vectors in the plane (u, v)
    # Use the first edge as u
    u = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
    len_u = sqrt(u[0]*u[0] + u[1]*u[1] + u[2]*u[2])
    if len_u > 1e-10:
        u = (u[0]/len_u, u[1]/len_u, u[2]/len_u)
    else:
        # fallback: use (1,0,0) as u
        u = (1.0, 0.0, 0.0)

    # v = normal × u
    v = (normal[1] * u[2] - normal[2] * u[1],
         normal[2] * u[0] - normal[0] * u[2],
         normal[0] * u[1] - normal[1] * u[0])
    len_v = sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if len_v > 1e-10:
        v = (v[0]/len_v, v[1]/len_v, v[2]/len_v)
    else:
        # fallback: use (0,1,0) as v
        v = (0.0, 1.0, 0.0)

    # Project the 3D points to 2D (u, v) coordinates
    pts_2d = []
    for p in pts_3d:
        dx = p.x - p0.x
        dy = p.y - p0.y
        dz = p.z - p0.z
        u_coord = dx * u[0] + dy * u[1] + dz * u[2]
        v_coord = dx * v[0] + dy * v[1] + dz * v[2]
        pts_2d.append(Point2D(u_coord, v_coord))

    # Triangulate the 2D polygon
    tri_indices_local = triangulate_polygon(pts_2d)  # returns indices into pts_2d

    # Convert local indices to original vertex indices
    triangles = []
    for tri in tri_indices_local:
        triangles.append((face_indices[tri[0]], face_indices[tri[1]], face_indices[tri[2]]))
    return triangles

# Pre Computing triangulation on all faces and returns a single flat list of triangles. Each triangle is a list of 3 vertex indices.
def precompute_triangles(vertices: list[Point3D], faces: list[list[int]]) -> list[list[int]]:
    
    all_triangles = []
    for face in faces:
        all_triangles.extend(triangulate_face(vertices, face))
    return all_triangles

def compute_vertex_normals(vertices, faces):
    """Compute per-vertex normals by averaging face normals."""
    normals = [Point3D(0, 0, 0) for _ in vertices]
    for face in faces:
        if len(face) < 3:
            continue
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        # Compute face normal
        edge1 = (v1.x - v0.x, v1.y - v0.y, v1.z - v0.z)
        edge2 = (v2.x - v0.x, v2.y - v0.y, v2.z - v0.z)
        nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
        ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
        nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]
        length = sqrt(nx*nx + ny*ny + nz*nz)
        if length > 1e-10:
            nx /= length; ny /= length; nz /= length
            for idx in face:
                normals[idx] = Point3D(normals[idx].x + nx,
                                       normals[idx].y + ny,
                                       normals[idx].z + nz)
    # Normalize all
    for i, n in enumerate(normals):
        length = sqrt(n.x*n.x + n.y*n.y + n.z*n.z)
        if length > 1e-10:
            normals[i] = Point3D(n.x/length, n.y/length, n.z/length)
        else:
            normals[i] = Point3D(0, 1, 0)
    return normals

#Transform normal cartesian coordinates from -1 ... 1 -> 0 ... 2 -> 0 ... 1 -> 0 ... window_width/height
def screenCoord(point:Point2D):
    return Point2D((point.x + 1)*window_width/2, (-point.y + 1)*window_height/2)

#Use x' = x/z and y' = y/z to obtain the projection of the corrected coordinates from the function above into the screen ("defining" a plane from where the drawings start being seen)
def projection(point:Point3D):
    return Point2D(point.x/point.z, point.y/point.z)

#Move point in a direction specified by the axis (0 = "x" Axis, 1 = "y" Axis, 2+ = "z" Axis)
def translation(point:Point3D, axis:int, deltaZ,):
    if axis == 0:
        return Point3D(point.x + deltaZ,point.y,point.z)
    elif axis == 1:
        return Point3D(point.x,point.y + deltaZ,point.z)
    return Point3D(point.x,point.y,point.z + deltaZ)

#Rotate point around a specified axis (0 = "x" Axis, 1 = "y" Axis, 2+ = "z" Axis)
def rotation(point:Point3D, axis:int, angle):
    if axis == 0:
        return Point3D(point.x,point.y*cos(angle) - point.z*sin(angle),point.y*sin(angle) + point.z*cos(angle))
    elif axis == 1:
        return Point3D(point.x*cos(angle) + point.z*sin(angle),point.y, -point.x*sin(angle) + point.z*cos(angle))
    return Point3D(point.x*cos(angle) - point.y*sin(angle),point.x*sin(angle)+ point.y*cos(angle),point.z)
