from math_utils import Point3D, compute_vertex_normals
from math import cos, sin, pi
import os
from materials import Material, DEFAULT_MAT

# Determine the directory where this file (model_loader.py) is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "Models")

#Parse a .mtl file and obtain a returned dict of materials
def load_mtl(filepath: str):
    materials = {}
    current_mat = None

    with open(filepath , "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) == 0:
                continue

            if parts[0] == "newmtl":
                name = parts[1]
                current_mat = Material(name = name)
                materials[name] = current_mat
            elif parts[0] == "Kd":
                if current_mat:
                    current_mat.diffuse = tuple(map(float , parts[1:4]))
            elif parts[0] == "Ka":
                if current_mat:
                    current_mat.ambient = tuple(map(float , parts[1:4]))
            elif parts[0] == "Ks":
                if current_mat:
                    current_mat.specular = tuple(map(float , parts[1:4]))
            elif parts[0] == "Ns":
                 if current_mat:
                    current_mat.shininess = float(parts[1])
            elif parts[0] == 'd' or parts[0] == "Tr":
                if current_mat:
                    if parts[0] == 'd':
                        current_mat.transparency = float(parts[1])
                    else:
                        current_mat.transparency = 1.0 - float(parts[1])

    return materials

# Completely define a solid using information from a .obj file
def load_obj(filename: str, scale_to_fit: float = 1.5) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    vertices = []
    normals = []          # raw model-space normals
    faces = []            # list of (vertex_indices, normal_indices)
    vertex_normals = []   # will map vertex index -> normal index (if provided)
    face_materials = []  # material name for each face (parallel to faces)
    current_material = None
    mtl_lib = None

    filepath = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if parts[0] == 'v':
                x, y, z = map(float, parts[1:4])
                vertices.append(Point3D(x, y, z))
            elif parts[0] == 'vn':
                x, y, z = map(float, parts[1:4])
                normals.append(Point3D(x, y, z))
            elif parts[0] == 'mtllib':
                mtl_lib = parts[1]
            elif parts[0] == 'usemtl':
                current_material = parts[1]
            elif parts[0] == 'f':
                # Parse face vertices & normals
                face_verts = []
                face_normals = []
                for token in parts[1:]:
                    # Token formats: "v", "v/vt", "v//vn", "v/vt/vn"
                    indices = token.split('/')
                    vi = int(indices[0]) - 1
                    face_verts.append(vi)
                    if len(indices) > 2 and indices[2] != '':
                        ni = int(indices[2]) - 1
                        face_normals.append(ni)
                    elif len(indices) > 1 and indices[1] == '':
                        # format: v//vn
                        ni = int(indices[2]) - 1
                        face_normals.append(ni)
                    else:
                        face_normals.append(None)  # no normal for this vertex
                faces.append((face_verts, face_normals))
                face_materials.append(current_material)

    # ---- Load materials ----
    materials = {}

    if mtl_lib:
        mtl_path = os.path.join(MODELS_DIR, mtl_lib)
        if os.path.exists(mtl_path):
            materials = load_mtl(mtl_path)

    if not vertices:
        return vertices, [], [], []
    if not faces:
        return vertices, [], [], [DEFAULT_MAT] * len(vertices)

    # ---- Center and scale vertices ----
    min_x = min(p.x for p in vertices)
    max_x = max(p.x for p in vertices)
    min_y = min(p.y for p in vertices)
    max_y = max(p.y for p in vertices)
    min_z = min(p.z for p in vertices)
    max_z = max(p.z for p in vertices)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    cz = (min_z + max_z) / 2.0

    max_extent = max(max_x - min_x, max_y - min_y, max_z - min_z)
    if max_extent == 0:
        max_extent = 1.0
    scale = scale_to_fit / max_extent

    for i, p in enumerate(vertices):
        vertices[i] = Point3D((p.x - cx) * scale, (p.y - cy) * scale, (p.z - cz) * scale)

    # ---- Build per-vertex normal list ----
    # If normals are missing, compute them from geometry
    vertex_normals = []
    if normals and all(n is not None for _, n_list in faces for n in n_list):
        # Use loaded normals
        for _, n_list in faces:
            for n_idx in n_list:
                if n_idx is not None:
                    vertex_normals.append(normals[n_idx])
        # Remove duplicates by building a map: vertex index -> normal index
        # Actually, we need to store normals per vertex, not per face.
        # Let's build a dict: vertex_idx -> normal
        normal_map = {}
        for v_list, n_list in faces:
            for vi, ni in zip(v_list, n_list):
                if ni is not None:
                    normal_map[vi] = normals[ni]
        vertex_normals = [normal_map.get(i, Point3D(0, 1, 0)) for i in range(len(vertices))]
    else:
        # Compute vertex normals from face normals (weighted average)
        vertex_normals = compute_vertex_normals(vertices, [v_list for v_list, _ in faces])

    # ---- Build material list per face ----
    face_material_objects = []
    for mat_name in face_materials:
        if mat_name and mat_name in materials:
            face_material_objects.append(materials[mat_name])
        else:
            face_material_objects.append(DEFAULT_MAT)

    # Convert faces to just vertex indices (for compatibility with existing code)
    faces_clean = [v_list for v_list, _ in faces]

    return vertices, faces_clean, vertex_normals, face_material_objects

def load_hexagonal_prism(base_radius: float = 0.7, half_height: float = 0.7) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    solid = []
    for i in range(6):
        angle = 2 * pi * i / 6
        solid.append(Point3D(base_radius * cos(angle), half_height, base_radius * sin(angle)))
    for i in range(6):
        angle = 2 * pi * i / 6
        solid.append(Point3D(base_radius * cos(angle), -half_height, base_radius * sin(angle)))

    faces = [
        [5, 4, 3, 2, 1, 0],
        [6, 7, 8, 9, 10, 11],
        [0, 1, 7, 6],
        [1, 2, 8, 7],
        [2, 3, 9, 8],
        [3, 4, 10, 9],
        [4, 5, 11, 10],
        [5, 0, 6, 11]
    ]
    vertex_normals = compute_vertex_normals(solid, faces)
    face_materials = [DEFAULT_MAT] * len(faces)
    return solid, faces, vertex_normals, face_materials

def load_cube(half: float = 0.5) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    solid = [
        Point3D( half,  half,  half),
        Point3D(-half,  half,  half),
        Point3D(-half, -half,  half),
        Point3D( half, -half,  half),
        Point3D( half,  half, -half),
        Point3D(-half,  half, -half),
        Point3D(-half, -half, -half),
        Point3D( half, -half, -half),
    ]
    faces = [
        [0,1,2,3],
        [5,4,7,6],
        [1,5,6,2],
        [3,7,4,0],
        [4,5,1,0],
        [3,2,6,7]
    ]
    vertex_normals = compute_vertex_normals(solid, faces)
    face_materials = [DEFAULT_MAT] * len(faces)
    return solid, faces, vertex_normals, face_materials

def load_icosahedron(scale: float = 0.5) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    phi = (1 + 5**0.5) / 2
    solid = [
        Point3D(0, 1*scale, phi*scale),
        Point3D(0, -1*scale, phi*scale),
        Point3D(0, 1*scale, -phi*scale),
        Point3D(0, -1*scale, -phi*scale),
        Point3D(1*scale, phi*scale, 0),
        Point3D(-1*scale, phi*scale, 0),
        Point3D(1*scale, -phi*scale, 0),
        Point3D(-1*scale, -phi*scale, 0),
        Point3D(phi*scale, 0, 1*scale),
        Point3D(-phi*scale, 0, 1*scale),
        Point3D(phi*scale, 0, -1*scale),
        Point3D(-phi*scale, 0, -1*scale),
    ]
    faces = [
        [0,5,9], [0,9,1], [0,1,8], [0,8,4], [0,4,5],
        [3,7,11], [3,11,2], [3,2,10], [3,10,6], [3,6,7],
        [5,11,9], [9,11,7], [9,7,1], [1,7,6], [1,6,8],
        [8,6,10], [8,10,4], [4,10,2], [4,2,5], [5,2,11]
    ]
    vertex_normals = compute_vertex_normals(solid, faces)
    face_materials = [DEFAULT_MAT] * len(faces)
    return solid, faces, vertex_normals, face_materials

def load_sphere(radius=1.5, num_lats=20, num_longs=20) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    vertices = []
    for i in range(num_lats + 1):
        theta = pi * i / num_lats
        for j in range(num_longs + 1):
            phi = 2 * pi * j / num_longs
            x = radius * sin(theta) * cos(phi)
            y = radius * cos(theta)
            z = radius * sin(theta) * sin(phi)
            vertices.append(Point3D(x, y, z))
    faces = []
    for i in range(num_lats):
        for j in range(num_longs):
            v1 = i * (num_longs + 1) + j
            v2 = i * (num_longs + 1) + (j + 1)
            v3 = (i + 1) * (num_longs + 1) + (j + 1)
            v4 = (i + 1) * (num_longs + 1) + j
            faces.append([v1, v2, v3, v4])
    vertex_normals = compute_vertex_normals(vertices, faces)
    face_materials = [DEFAULT_MAT] * len(faces)
    return vertices, faces, vertex_normals, face_materials

def load_torus(major_radius=1, minor_radius=0.2, num_rings=40, num_segments=15) -> tuple[list[Point3D], list[list[int]], list[Point3D], list[Material]]:
    vertices = []
    for i in range(num_rings):
        theta = 2 * pi * i / num_rings
        for j in range(num_segments):
            phi = 2 * pi * j / num_segments
            x = (major_radius + minor_radius * cos(phi)) * cos(theta)
            y = (major_radius + minor_radius * cos(phi)) * sin(theta)
            z = minor_radius * sin(phi)
            vertices.append(Point3D(x, y, z))
    faces = []
    for i in range(num_rings):
        for j in range(num_segments):
            v1 = i * num_segments + j
            v2 = i * num_segments + (j + 1) % num_segments
            v3 = ((i + 1) % num_rings) * num_segments + (j + 1) % num_segments
            v4 = ((i + 1) % num_rings) * num_segments + j
            faces.append([v1, v2, v3, v4])
    vertex_normals = compute_vertex_normals(vertices, faces)
    face_materials = [DEFAULT_MAT] * len(faces)
    return vertices, faces, vertex_normals, face_materials
