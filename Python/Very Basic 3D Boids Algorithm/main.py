from ursina import *  # type: ignore
import random
import math
import ctypes
import numpy as np
import os
import sys

# ------------------------------------------------------------
# Global simulation parameters
# ------------------------------------------------------------
separation_weight = 1.6
alignment_weight = 1.05
cohesion_weight = 0.85
SHOW_VISUALS = False
BOUNDING_BOX_ENABLED = True
BOUNDS = 10
CELL_SIZE = 5
MAX_BOIDS = 1500

# ------------------------------------------------------------
# Fixed (scalar) behavior limits
# ------------------------------------------------------------
MAX_FORCE = 0.5
MAX_SPEED = 2.0

# ------------------------------------------------------------
# Ursina app and camera
# ------------------------------------------------------------
app = Ursina()
camera = EditorCamera()
camera.position = Vec3(15, 10, 15)
camera.look_at(Vec3(-1, -0.66, -1))

# ------------------------------------------------------------
# UI sliders
# ------------------------------------------------------------
def set_separation():
    global separation_weight
    separation_weight = sep_slider.value

def set_alignment():
    global alignment_weight
    alignment_weight = ali_slider.value

def set_cohesion():
    global cohesion_weight
    cohesion_weight = coh_slider.value

sep_slider = Slider(text="Separation", min=0.0, max=2.0, default=separation_weight, #type: ignore
                    step=0.01, x=-0.65, y=0.45,
                    on_value_changed=set_separation, scale=0.5, dynamic=True)
ali_slider = Slider(text="Alignment", min=0.0, max=2.0, default=alignment_weight, #type: ignore
                    step=0.01, x=-0.65, y=0.35,
                    on_value_changed=set_alignment, scale=0.5, dynamic=True)
coh_slider = Slider(text="Cohesion", min=0.0, max=2.0, default=cohesion_weight, #type: ignore
                    step=0.01, x=-0.65, y=0.25,
                    on_value_changed=set_cohesion, scale=0.5, dynamic=True)

# ------------------------------------------------------------
# Input handling
# ------------------------------------------------------------
def input(key):
    global SHOW_VISUALS, BOUNDING_BOX_ENABLED
    if key == 'v':
        SHOW_VISUALS = not SHOW_VISUALS
        for boid in Boid.all_entities:
            boid.sep_visual.enabled = SHOW_VISUALS
    elif key == 'b':
        BOUNDING_BOX_ENABLED = not BOUNDING_BOX_ENABLED
        wireframe_cube.enabled = BOUNDING_BOX_ENABLED

# ------------------------------------------------------------
# Spatial grid (stores indices, not entities)
# ------------------------------------------------------------
class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}          # key: (cx, cy, cz) -> list of boid indices

    def clear(self):
        self.cells.clear()

    def _cell_key(self, pos):
        return (int(pos[0] // self.cell_size),
                int(pos[1] // self.cell_size),
                int(pos[2] // self.cell_size))

    def insert(self, index):
        key = self._cell_key(positions[index])
        self.cells.setdefault(key, []).append(index)

    def get_nearby(self, index, radius):
        center = self._cell_key(positions[index])
        candidates = []
        search_range = int(radius // self.cell_size) + 1
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                for dz in range(-search_range, search_range + 1):
                    key = (center[0] + dx, center[1] + dy, center[2] + dz)
                    if key in self.cells:
                        candidates.extend(self.cells[key])
        return candidates

grid = SpatialGrid(CELL_SIZE)

# ------------------------------------------------------------
# Numpy arrays for simulation state (source of truth)
# ------------------------------------------------------------
n_boids = MAX_BOIDS
positions = np.random.uniform(-BOUNDS, BOUNDS, (n_boids, 3)).astype(np.float32)
velocities = np.random.uniform(-1, 1, (n_boids, 3)).astype(np.float32)

# Individual parameters (can be randomized per boid)
vision_radii = np.random.uniform(1.5, 2.5, n_boids).astype(np.float32)
separation_radii = np.random.uniform(0.55, 1.05, n_boids).astype(np.float32)

# Pre‑allocated output arrays for steering forces
sep_steer = np.zeros((n_boids, 3), dtype=np.float32)
ali_steer = np.zeros((n_boids, 3), dtype=np.float32)
coh_steer = np.zeros((n_boids, 3), dtype=np.float32)

# ------------------------------------------------------------
# Load C library (with fallback to Python)
# ------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.platform == 'win32':
    lib_path = os.path.join(script_dir, 'flock.dll')
else:
    lib_path = os.path.join(script_dir, 'libflock.so')

lib = None
try:
    lib = ctypes.CDLL(lib_path)
    print(f"C flocking library loaded from {lib_path}")
except OSError:
    print(f"C library not found at {lib_path} – using Python fallback for force calculation.")

if lib is not None:
    lib.compute_flocking_forces.argtypes = [
        ctypes.POINTER(ctypes.c_float),  # positions
        ctypes.POINTER(ctypes.c_float),  # velocities
        ctypes.POINTER(ctypes.c_float),  # vision_radii
        ctypes.POINTER(ctypes.c_float),  # separation_radii
        ctypes.c_float,                  # max_force (scalar)
        ctypes.c_float,                  # max_speed (scalar)
        ctypes.POINTER(ctypes.c_int),    # neighbor_indices
        ctypes.POINTER(ctypes.c_int),    # neighbor_offsets
        ctypes.c_int,                    # n
        ctypes.POINTER(ctypes.c_float),  # out_sep
        ctypes.POINTER(ctypes.c_float),  # out_ali
        ctypes.POINTER(ctypes.c_float)   # out_coh
    ]
    lib.compute_flocking_forces.restype = None
#lib = None
# ------------------------------------------------------------
# Boid entity (visual only)
# ------------------------------------------------------------
class Boid(Entity):
    all_entities = []   # list of Boid entities for rendering

    def __init__(self, index):
        super().__init__(
            model='cube',
            scale=0.2,
            color=color.black,
            position=Vec3(positions[index, 0], positions[index, 1], positions[index, 2])
        )
        self.index = index
        self.velocity = Vec3(velocities[index, 0], velocities[index, 1], velocities[index, 2])
        self.sep_visual = SeparationVisualizer(self)
        Boid.all_entities.append(self)

    def update_visuals(self):
        self.position = Vec3(
            float(positions[self.index, 0]),
            float(positions[self.index, 1]),
            float(positions[self.index, 2])
        )
        self.velocity = Vec3(
            float(velocities[self.index, 0]),
            float(velocities[self.index, 1]),
            float(velocities[self.index, 2])
        )
        speed = self.velocity.length()
        if speed > 0.001:
            self.look_at(self.position + self.velocity)
    
        r = max(0.0, min(1.0, (self.x + BOUNDS) / (2 * BOUNDS)))
        g = max(0.0, min(1.0, (self.y + BOUNDS) / (2 * BOUNDS)))
        b = max(0.0, min(1.0, (self.z + BOUNDS) / (2 * BOUNDS)))
        self.color = color.rgb(float(r), float(g), float(b))

# ------------------------------------------------------------
# Separation visualizer (debug sphere)
# ------------------------------------------------------------
class SeparationVisualizer(Entity):
    def __init__(self, boid):
        super().__init__(
            parent=boid,
            model='sphere',
            scale=float(separation_radii[boid.index] * 2 / 0.2),
            color=color.rgb(70, 70, 70),
            unlit=True,
            alpha=0.2,
            enabled=SHOW_VISUALS
        )

    def update(self):
        if self.enabled:
            self.color = self.parent.color
            self.alpha = 0.2

# ------------------------------------------------------------
# Python fallback force calculation (if C lib missing)
# ------------------------------------------------------------
def compute_forces_python(neighbor_indices, neighbor_offsets):
    # Zero outputs
    sep_steer.fill(0)
    ali_steer.fill(0)
    coh_steer.fill(0)

    for i in range(n_boids):
        px, py, pz = positions[i]
        vx, vy, vz = velocities[i]
        vision_r = vision_radii[i]
        sep_r = separation_radii[i]

        start = neighbor_offsets[i]
        end = neighbor_offsets[i+1]

        count_sep = 0
        count_ali = 0
        count_coh = 0

        for idx in range(start, end):
            j = neighbor_indices[idx]
            if j == i:
                continue   # skip self

            dx = px - positions[j, 0]
            dy = py - positions[j, 1]
            dz = pz - positions[j, 2]
            d_sq = dx*dx + dy*dy + dz*dz

            # Separation
            if d_sq > 0 and d_sq < sep_r * sep_r:
                d = math.sqrt(d_sq)
                inv_d_sq = 1.0 / d_sq
                sep_steer[i, 0] += dx / d * inv_d_sq
                sep_steer[i, 1] += dy / d * inv_d_sq
                sep_steer[i, 2] += dz / d * inv_d_sq
                count_sep += 1

            # Alignment
            if d_sq < vision_r * vision_r:
                ali_steer[i, 0] += velocities[j, 0]
                ali_steer[i, 1] += velocities[j, 1]
                ali_steer[i, 2] += velocities[j, 2]
                count_ali += 1

                coh_steer[i, 0] += positions[j, 0]
                coh_steer[i, 1] += positions[j, 1]
                coh_steer[i, 2] += positions[j, 2]
                count_coh += 1

        # Finalize separation
        if count_sep > 0:
            sep_steer[i] /= count_sep
            norm = np.linalg.norm(sep_steer[i])
            if norm > 1e-6:
                sep_steer[i] = sep_steer[i] / norm * MAX_SPEED
                sep_steer[i, 0] -= vx
                sep_steer[i, 1] -= vy
                sep_steer[i, 2] -= vz
                norm = np.linalg.norm(sep_steer[i])
                if norm > MAX_FORCE:
                    sep_steer[i] *= MAX_FORCE / norm

        # Finalize alignment
        if count_ali > 0:
            ali_steer[i] /= count_ali
            norm = np.linalg.norm(ali_steer[i])
            if norm > 1e-6:
                ali_steer[i] = ali_steer[i] / norm * MAX_SPEED
                ali_steer[i, 0] -= vx
                ali_steer[i, 1] -= vy
                ali_steer[i, 2] -= vz
                norm = np.linalg.norm(ali_steer[i])
                if norm > MAX_FORCE:
                    ali_steer[i] *= MAX_FORCE / norm

        # Finalize cohesion
        if count_coh > 0:
            coh_steer[i] /= count_coh
            desired = coh_steer[i] - positions[i]
            norm = np.linalg.norm(desired)
            if norm > 1e-6:
                desired = desired / norm * MAX_SPEED
                coh_steer[i, 0] = desired[0] - vx
                coh_steer[i, 1] = desired[1] - vy
                coh_steer[i, 2] = desired[2] - vz
                norm = np.linalg.norm(coh_steer[i])
                if norm > MAX_FORCE:
                    coh_steer[i] *= MAX_FORCE / norm

# ------------------------------------------------------------
# Collision resolution (impulse + positional correction)
# ------------------------------------------------------------
def resolve_boid_collisions():
    # Use spatial grid to find candidate pairs
    for i in range(n_boids):
        # Only check pairs once (i < j) by using grid and id check
        nearby = grid.get_nearby(i, 0.3)  # collision radius * 2
        for j in nearby:
            if j <= i:  # avoid double resolution
                continue
            dx = positions[j, 0] - positions[i, 0]
            dy = positions[j, 1] - positions[i, 1]
            dz = positions[j, 2] - positions[i, 2]
            d_sq = dx*dx + dy*dy + dz*dz
            min_dist = 0.3  # collision_radius * 2 = 0.15 * 2
            if d_sq < min_dist * min_dist and d_sq > 0:
                d = math.sqrt(d_sq)
                nx, ny, nz = dx / d, dy / d, dz / d
                # Relative velocity along normal
                rvx = velocities[j, 0] - velocities[i, 0]
                rvy = velocities[j, 1] - velocities[i, 1]
                rvz = velocities[j, 2] - velocities[i, 2]
                vel_along_n = rvx * nx + rvy * ny + rvz * nz
                if vel_along_n < 0:
                    # Impulse (equal mass, restitution = 0.5)
                    j_impulse = -(1 + 0.5) * vel_along_n / 2
                    velocities[i, 0] -= j_impulse * nx
                    velocities[i, 1] -= j_impulse * ny
                    velocities[i, 2] -= j_impulse * nz
                    velocities[j, 0] += j_impulse * nx
                    velocities[j, 1] += j_impulse * ny
                    velocities[j, 2] += j_impulse * nz
                # Positional correction
                overlap = min_dist - d
                correction = overlap * 0.5
                positions[i, 0] -= nx * correction
                positions[i, 1] -= ny * correction
                positions[i, 2] -= nz * correction
                positions[j, 0] += nx * correction
                positions[j, 1] += ny * correction
                positions[j, 2] += nz * correction

# ------------------------------------------------------------
# Global update loop
# ------------------------------------------------------------
def update():
    global positions, velocities
    # 1. Rebuild spatial grid from current positions
    grid.clear()
    for i in range(n_boids):
        grid.insert(i)

    # 2. Build neighbor indices and offsets
    neighbor_indices = []
    neighbor_offsets = [0]
    for i in range(n_boids):
        # Use vision_radius for neighbor search; we'll filter inside C/Python
        nearby = grid.get_nearby(i, vision_radii[i])
        neighbor_indices.extend(nearby)
        neighbor_offsets.append(len(neighbor_indices))

    neighbor_indices_arr = np.ascontiguousarray(neighbor_indices, dtype=np.int32)
    neighbor_offsets_arr = np.ascontiguousarray(neighbor_offsets, dtype=np.int32)

    # 3. Compute steering forces (C or Python)
    if lib is not None:
        lib.compute_flocking_forces(
            positions.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            velocities.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            vision_radii.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            separation_radii.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_float(MAX_FORCE),
            ctypes.c_float(MAX_SPEED),
            neighbor_indices_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            neighbor_offsets_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            ctypes.c_int(n_boids),
            sep_steer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ali_steer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            coh_steer.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        )
    else:
        compute_forces_python(neighbor_indices_arr, neighbor_offsets_arr)

    # 4. Apply weighted forces to velocities
    velocities += sep_steer * separation_weight #type: ignore
    velocities += ali_steer * alignment_weight #type: ignore
    velocities += coh_steer * cohesion_weight #type: ignore

    # 5. Limit speeds
    speeds = np.linalg.norm(velocities, axis=1)
    mask = speeds > MAX_SPEED
    velocities[mask] = (velocities[mask].T / speeds[mask]).T * MAX_SPEED

    # 6. Update positions
    positions += velocities * time.dt #type: ignore

    # 7. Wrap around bounds if enabled
    if BOUNDING_BOX_ENABLED:
        positions[positions > BOUNDS] = -BOUNDS
        positions[positions < -BOUNDS] = BOUNDS

    # 8. Resolve collisions
    #resolve_boid_collisions()

    # 9. Update visual entities
    for boid in Boid.all_entities:
        boid.update_visuals()

# ------------------------------------------------------------
# Create boids and bounding box
# ------------------------------------------------------------
for i in range(n_boids):
    Boid(i)

wireframe_cube = Entity(model='cube', scale=BOUNDS * 2, color=color.white,
                        wireframe=True, double_sided=True)

# ------------------------------------------------------------
# Run the app
# ------------------------------------------------------------
app.run()