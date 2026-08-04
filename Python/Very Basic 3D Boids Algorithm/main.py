from ursina import * # type: ignore
import random

app = Ursina()

SEPARATION_WEIGHT = 0.3
ALIGNMENT_WEIGHT = 0.2
COHESION_WEIGHT = 0.1
SHOW_VISUALS = True

def input(key):
    global SHOW_VISUALS
    if key == 'v':
        SHOW_VISUALS = not SHOW_VISUALS
        for boid in Boid.all_boids:
            boid.sep_visual.enabled = SHOW_VISUALS   # stops rendering completely

class SeparationVisualizer(Entity):
    def __init__(self, boid):
        super().__init__(
            parent=boid,
            model='sphere',
            scale=boid.separation_radius * 2/0.2,
            color=color.rgb(70, 70, 70),   # red, 60 alpha
            unlit=True,
            alpha=0.2                          # enables alpha blending
        )
    

class Boid(Entity):
    all_boids = []
    def __init__(self):
        super().__init__(
            model='cube', 
            scale=0.2,
            color=color.black,
            position=(random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))
        )
        self.velocity = Vec3(0.0,0.0,0.0)#Vec3(random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))

        # Experimenting using slightly random values in hopes it'll mimic individuality even among same species individuals
        self.vision_radius = random.uniform(1.8,2.2) #defining how far in a circle/sphere each boid can see
        self.separation_radius = random.uniform(0.9,1.1) #defining a circle/sphere limit from where the boid starts to avoid others so no bumping occurs
        self.max_force = 0.5
        self.max_speed = 2.0

        self.sep_visual = SeparationVisualizer(self)
        
        Boid.all_boids.append(self)

    def calc_separation(self):
        steer = Vec3(0,0,0)
        count = 0

        for other in Boid.all_boids:
            if other is self:
                continue
            d = distance(self,other)
            if 0 < d < self.separation_radius:
                diff = self.position - other.position
                diff.normalize()
                diff /= d
                steer += diff
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


    def calc_alignment(self):
        avg_velocity = Vec3(0,0,0)
        count = 0

        for other in Boid.all_boids:
            if other is self: 
                continue
            if distance(self, other) < self.vision_radius:
                avg_velocity += Vec3(0,0,0)
        pass

    def calc_cohesion(self):
        pass
    
        
    def update(self):

        sep = self.calc_separation() * SEPARATION_WEIGHT

        self.velocity += sep # type: ignore # Add "- self.velocity*0.1" if you want them to lose speed after separating and trully check of the movement was just due to it

        if self.velocity.length() > self.max_speed: # type: ignore
            self.velocity.normalize() # type: ignore
            self.velocity *= self.max_speed # type: ignore
        
        self.position += self.velocity * time.dt # type: ignore 
    
        r = max(0,min(1,(self.x + 1)/2))
        g = max(0,min(1,(self.y + 1)/2))
        b = max(0,min(1,(self.z + 1)/2))

        self.color = color.rgb(r, g, b)


camera = EditorCamera()


boids = [Boid() for _ in range(3)]

Entity(model='plane', scale=10, color=color.gray, texture='white_cube',)

app.run()