from math_utils import Point2D, Point3D
from math import cos, sin, pi
import os

# Get the directory where this file (model_loader.py) is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Models folder is in the same directory as model_loader.py (or one level up?)
# Usually, model_loader.py is in the same folder as main.py, so:
MODELS_DIR = os.path.join(SCRIPT_DIR, "Models")

# Completely define a solid using information from a .obj file
def load_obj(filename:str, scale_to_fit = 1.5) -> tuple[list[Point3D], list[list[int]]]:

    #Get the file 
    filepath = os.path.join(MODELS_DIR, filename)
    print(f"Attempting to load: {filepath}")   # temporary debug
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    vertices_list, faces_list = [], []
    with open(filepath,"r") as file:

        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if line.startswith("v "):
                x, y, z = map(float,parts[1:4])
                vertices_list.append(Point3D(x,y,z))
            
            if line.startswith("f "):
                faces = parts[1:]
                face_indexes = []
                for vert in faces:
                    v_index = int(vert.split("/")[0]) - 1 #bcs .obj files use lists starting at index 1
                    face_indexes.append(v_index)
                faces_list.append(face_indexes)
    
    #Center the Model
    min_x = min(p.x for p in vertices_list)
    min_y = min(p.y for p in vertices_list)
    min_z = min(p.z for p in vertices_list)

    max_x = max(p.x for p in vertices_list)
    max_y = max(p.y for p in vertices_list)
    max_z = max(p.z for p in vertices_list)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    cz = (min_z + max_z) / 2.0

    max_extent = max(max_x - min_x, max_y - min_y, max_z - min_z)
    if max_extent == 0:
        max_extent = 1.0
    scale = scale_to_fit / max_extent

    #Scalling and translation to the correct place
    for i , p in enumerate(vertices_list):
        vertices_list[i] = Point3D(
             (p.x - cx) * scale,
             (p.y - cy) * scale,
             (p.z - cz) * scale 
            )

    return vertices_list , faces_list

def load_hexagonal_prism(base_radius:float = 0.7, half_height:float = 0.7) -> tuple[list[Point3D], list[list[int]]]:
    #NOTE: THIS WAS OBTAINED THROUGH A PROMPT ASKING FOR MORE MODELS TO TEST THE CODE WITH
    solid = []

    # Top face (y = +h)
    for i in range(6):
        angle = 2 * pi * i / 6
        solid.append(Point3D(base_radius * cos(angle), half_height, base_radius * sin(angle)))

    # Bottom face (y = -h)
    for i in range(6):
        angle = 2 * pi * i / 6
        solid.append(Point3D(base_radius * cos(angle), -half_height, base_radius * sin(angle)))

    # Vertices 0–5 = top, 6–11 = bottom
    faces = [
        [5, 4, 3, 2, 1, 0],          # Top face (fixed: outward +Y)
        [6, 7, 8, 9, 10, 11],        # Bottom face (unchanged: outward -Y)
        [0, 1, 7, 6],                # Side 1
        [1, 2, 8, 7],                # Side 2
        [2, 3, 9, 8],                # Side 3
        [3, 4, 10, 9],               # Side 4
        [4, 5, 11, 10],              # Side 5
        [5, 0, 6, 11]                # Side 6
    ]

    return solid, faces

def load_cube(half:float = 0.5) -> tuple[list[Point3D], list[list[int]]]:

    solid = [
        Point3D(half,half,half),
        Point3D(-half,half,half),
        Point3D(-half,-half,half),
        Point3D(half,-half,half),

        Point3D(half,half,-half),
        Point3D(-half,half,-half),
        Point3D(-half,-half,-half),
        Point3D(half,-half,-half),
    ]

    faces = [
        [0,1,2,3], # Back Face (z = half + starting_plane) - Farthest from camera/user (at/close to z = 0) (Normal: +Z) - Away from camera
        [5,4,7,6], # Front Face (z = -half + starting_plane) - Farthest from camera/user (Normal: -Z) - Towards camera
        [1,5,6,2], # Left Face (x = -half) (Normal: -X)
        [3,7,4,0], # Right Face (x = +half) (Normal: +X)
        [4,5,1,0], # Top Face (y = +half) (Normal: +Y)
        [3,2,6,7], # Bottom Face (y = -half) (Normal: -Y)
    ]

    return solid, faces

def load_icosahedron(scale:float = 0.5) -> tuple[list[Point3D], list[list[int]]]:
    #NOTE: THIS WAS OBTAINED THROUGH A PROMPT ASKING FOR MORE MODELS TO TEST THE CODE WITH

    # ---------- ICOSAHEDRON (20 triangular faces) ----------
    phi = (1 + 5**0.5) / 2   # golden ratio ~1.618
    solid = [
        Point3D(0, 1*scale, phi*scale),    # 0
        Point3D(0, -1*scale, phi*scale),   # 1
        Point3D(0, 1*scale, -phi*scale),   # 2
        Point3D(0, -1*scale, -phi*scale),  # 3
        Point3D(1*scale, phi*scale, 0),    # 4
        Point3D(-1*scale, phi*scale, 0),   # 5
        Point3D(1*scale, -phi*scale, 0),   # 6
        Point3D(-1*scale, -phi*scale, 0),  # 7
        Point3D(phi*scale, 0, 1*scale),    # 8
        Point3D(-phi*scale, 0, 1*scale),   # 9
        Point3D(phi*scale, 0, -1*scale),   # 10
        Point3D(-phi*scale, 0, -1*scale),  # 11
    ]

    faces = [
        # 5 triangles meeting at vertex 0 (top cap)
        [0, 5, 9],
        [0, 9, 1],
        [0, 1, 8],
        [0, 8, 4],
        [0, 4, 5],
        # 5 triangles meeting at vertex 3 (bottom cap)
        [3, 7, 11],
        [3, 11, 2],
        [3, 2, 10],
        [3, 10, 6],
        [3, 6, 7],
        # 10 triangles in the belt (middle ring)
        [5, 11, 9],
        [9, 11, 7],
        [9, 7, 1],
        [1, 7, 6],
        [1, 6, 8],
        [8, 6, 10],
        [8, 10, 4],
        [4, 10, 2],
        [4, 2, 5],
        [5, 2, 11],
    ]
    return solid, faces

def load_sphere(radius:float = 1.5, num_lats:int = 20, num_longs:int = 20) -> tuple[list[Point3D], list[list[int]]]:
    #NOTE: THIS WAS OBTAINED THROUGH A PROMPT ASKING FOR MORE MODELS TO TEST THE CODE WITH
    vertices = []
    faces = []
    
    for i in range(num_lats + 1):
        theta = pi * i / num_lats  # from 0 to pi (top to bottom)
        for j in range(num_longs + 1):
            phi = 2 * pi * j / num_longs  # around the equator
            x = radius * sin(theta) * cos(phi)
            y = radius * cos(theta)
            z = radius * sin(theta) * sin(phi)
            vertices.append(Point3D(x, y, z))
    
    for i in range(num_lats):
        for j in range(num_longs):
            v1 = i * (num_longs + 1) + j
            v2 = i * (num_longs + 1) + (j + 1)
            v3 = (i + 1) * (num_longs + 1) + (j + 1)
            v4 = (i + 1) * (num_longs + 1) + j
            faces.append([v1, v2, v3, v4])
    
    return vertices, faces
    
def load_torus(major_radius:float = 1, minor_radius:float = 0.2, num_rings:int = 40, num_segments:int = 15) -> tuple[list[Point3D], list[list[int]]]:
    #NOTE: THIS WAS OBTAINED THROUGH A PROMPT ASKING FOR MORE MODELS TO TEST THE CODE WITH
    """
    major_radius: distance from center of hole to center of tube
    minor_radius: radius of the tube itself
    num_rings:    number of divisions around the main ring (longitude), in how many sections the tube will be built, like slices of a cake 
    num_segments: number of divisions around the tube (latitude), in how many points will be defined the circunferences of the tube
    """
    vertices = []
    faces = []
    
    for i in range(num_rings):
        theta = 2 * pi * i / num_rings  # angle around the main ring
        for j in range(num_segments):
            phi = 2 * pi * j / num_segments  # angle around the tube
            
            # Parametric equation of a torus
            x = (major_radius + minor_radius * cos(phi)) * cos(theta)
            y = (major_radius + minor_radius * cos(phi)) * sin(theta)
            z = minor_radius * sin(phi)
            
            vertices.append(Point3D(x, y, z))
    
    # Build quad faces (4 vertices each)
    for i in range(num_rings):
        for j in range(num_segments):
            v1 = i * num_segments + j
            v2 = i * num_segments + (j + 1) % num_segments
            v3 = ((i + 1) % num_rings) * num_segments + (j + 1) % num_segments
            v4 = ((i + 1) % num_rings) * num_segments + j
            faces.append([v1, v2, v3, v4])
    
    return vertices, faces

def load_l_shape():
    solid = [
        Point3D(-1, -1, 0),
        Point3D( 1, -1, 0),
        Point3D( 1,  0, 0),
        Point3D( 0,  0, 0),
        Point3D( 0,  1, 0),
        Point3D(-1,  1, 0),
    ]
    faces = [[0,1,2,3,4,5]]
    return solid, faces
