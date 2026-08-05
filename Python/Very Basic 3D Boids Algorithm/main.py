from ursina import *  # type: ignore
import random

separation_weight = 0.3
alignment_weight = 0.3
cohesion_weight = 0.2
SHOW_VISUALS = False
BOUNDING_BOX_ENABLED = True
BOUNDS = 5
CELL_SIZE = 3

app = Ursina()

def set_separation():
    global separation_weight
    separation_weight = sep_slider.value

def set_alignment():
    global alignment_weight
    alignment_weight = ali_slider.value

def set_cohesion():
    global cohesion_weight
    cohesion_weight = coh_slider.value

sep_slider = Slider(
    text="Separation",
    min=0.0, max=2.0, default=separation_weight, # type: ignore
    step=0.01,
    x=-0.65, y=0.45,
    on_value_changed=set_separation,
    parent=camera.ui,
    scale=0.5
)

ali_slider = Slider(
    text="Alignment",
    min=0.0, max=2.0, default=alignment_weight, # type: ignore
    step=0.01,
    x=-0.65, y=0.35,
    on_value_changed=set_alignment,
    parent=camera.ui,
    scale=0.5
)

coh_slider = Slider(
    text="Cohesion",
    min=0.0, max=2.0, default=cohesion_weight, # type: ignore
    step=0.01,
    x=-0.65, y=0.25,
    on_value_changed=set_cohesion,
    parent=camera.ui,
    scale=0.5
)

def input(key):
    global SHOW_VISUALS
    if key == 'v':
        SHOW_VISUALS = not SHOW_VISUALS
        for boid in Boid.all_boids:
            boid.sep_visual.enabled = SHOW_VISUALS
    global BOUNDING_BOX_ENABLED
    if key == 'b':
        BOUNDING_BOX_ENABLED = not BOUNDING_BOX_ENABLED
        wireframe_cube.enabled = BOUNDING_BOX_ENABLED

class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}          # key: (cx, cy, cz) -> list of boids

    def clear(self):
        self.cells.clear()

    def get_cell_key(self, position):
        return (int(position.x // self.cell_size),
                int(position.y // self.cell_size),
                int(position.z // self.cell_size))

    def insert(self, boid):
        key = self.get_cell_key(boid.position)
        self.cells.setdefault(key, []).append(boid)   # fixed typo

    def get_nearby(self, boid, radius):
        center = self.get_cell_key(boid.position)
        candidates = []
        search_range = int(radius // self.cell_size) + 1
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                for dz in range(-search_range, search_range + 1):
                    key = (center[0] + dx, center[1] + dy, center[2] + dz)
                    if key in self.cells:
                        candidates.extend(self.cells[key])
        return candidates
    
class SeparationVisualizer(Entity):
    def __init__(self, boid):
        super().__init__(
            parent=boid,
            model='sphere',
            scale=boid.separation_radius * 2 / 0.2,   # your custom scaling
            color=color.rgb(70, 70, 70),
            unlit=True,
            alpha=0.2,
            enabled=SHOW_VISUALS
        )
    def update(self):
        self.color = self.parent.color
        self.alpha = 0.2

grid = SpatialGrid(CELL_SIZE)

class Boid(Entity):
    all_boids = []

    def __init__(self):
        super().__init__(
            model='cube',
            scale=0.2,
            color=color.black,
            position=(random.uniform(-BOUNDS/2, BOUNDS/2),
                      random.uniform(-BOUNDS/2, BOUNDS/2),
                      random.uniform(-BOUNDS/2, BOUNDS/2))
        )
        self.velocity = Vec3(random.uniform(-1, 1),
                             random.uniform(-1, 1),
                             random.uniform(-1, 1))

        # individuality parameters
        self.vision_radius = random.uniform(1.5, 2.5)
        self.separation_radius = random.uniform(0.55, 1.05)
        self.max_force = 0.5
        self.max_speed = 2.0

        self.sep_visual = SeparationVisualizer(self)

        Boid.all_boids.append(self)

    def calc_separation(self, nearby):
        steer = Vec3(0, 0, 0)
        count = 0
        sep_radius_sq = self.separation_radius ** 2
        for other in nearby:
            if other is self:
                continue
            offset = self.position - other.position
            d_sq = offset.length_squared()
            if 0 < d_sq < sep_radius_sq:
                # use 1/d² weighting – no sqrt
                offset.normalize()
                steer += offset / d_sq
                count += 1
        if count > 0:
            steer /= count
            steer.normalize()
            steer *= self.max_speed
            steer -= self.velocity
            if steer.length() > self.max_force:
                steer.normalize()
                steer *= self.max_force
        return steer

    def calc_alignment(self, nearby):
        avg_velocity = Vec3(0, 0, 0)
        count = 0
        vision_radius_sq = self.vision_radius ** 2
        for other in nearby:
            if other is self:
                continue
            offset = self.position - other.position
            if offset.length_squared() < vision_radius_sq:
                avg_velocity += other.velocity
                count += 1
        if count > 0:
            avg_velocity /= count
            avg_velocity.normalize()
            avg_velocity *= self.max_speed
            steer = avg_velocity - self.velocity
            if steer.length() > self.max_force:
                steer.normalize()
                steer *= self.max_force
            return steer
        return Vec3(0, 0, 0)

    def calc_cohesion(self, nearby):
        center = Vec3(0, 0, 0)
        count = 0
        vision_radius_sq = self.vision_radius ** 2
        for other in nearby:
            if other is self:
                continue
            offset = self.position - other.position
            if offset.length_squared() < vision_radius_sq:
                center += other.position
                count += 1
        if count > 0:
            center /= count
            desired = center - self.position
            desired.normalize()
            desired *= self.max_speed
            steer = desired - self.velocity
            if steer.length() > self.max_force:
                steer.normalize()
                steer *= self.max_force
            return steer
        return Vec3(0, 0, 0)

    def apply_flocking(self, grid):
        nearby = grid.get_nearby(self, self.vision_radius)

        sep = self.calc_separation(nearby) * separation_weight
        ali = self.calc_alignment(nearby) * alignment_weight
        coh = self.calc_cohesion(nearby) * cohesion_weight

        self.velocity += sep + ali + coh

        # limit speed
        if self.velocity.length() > self.max_speed: # type: ignore
            self.velocity.normalize() # type: ignore
            self.velocity *= self.max_speed # type: ignore

        self.position += self.velocity * time.dt  # type: ignore

        if self.velocity.length() > 0:   # avoid zero‑vector errors # type: ignore
            self.look_at(self.position + self.velocity)

        # wrap around the bounded world
        if BOUNDING_BOX_ENABLED:
            for attr in ('x', 'y', 'z'):
                val = getattr(self, attr)
                if val > BOUNDS:
                    setattr(self, attr, -BOUNDS)
                elif val < -BOUNDS:
                    setattr(self, attr, BOUNDS)

        # colour based on position (rainbow across the world)
        r = max(0, min(1, (self.x + BOUNDS) / (2 * BOUNDS)))
        g = max(0, min(1, (self.y + BOUNDS) / (2 * BOUNDS)))
        b = max(0, min(1, (self.z + BOUNDS) / (2 * BOUNDS)))
        self.color = color.rgb(r, g, b)

# Ursina automatically calls this global update() every frame
def update():
    grid.clear()
    for boid in Boid.all_boids:
        grid.insert(boid)
    for boid in Boid.all_boids:
        boid.apply_flocking(grid)


camera = EditorCamera() 

boids = [Boid() for _ in range(180)]
wireframe_cube = Entity(model='cube', scale=BOUNDS * 2, color=color.white, wireframe=True, double_sided= True)


app.run()