from ursina import * # type: ignore
import random

app = Ursina()

class Boid(Entity):
    def __init__(self):
        super().__init__(
            model='cube', 
            scale=0.2,
            color=color.black,
            position=(random.uniform(-3,3),random.uniform(-3,3),random.uniform(-3,3))
        )
        self.velocity = Vec3(random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))
        
    def update(self):
        
        self.position += self.velocity * 0.001
        self.velocity[0] += random.uniform(-1/5,1/5) 
        self.velocity[1] += random.uniform(-1/5,1/5) 
        self.velocity[2] += random.uniform(-1/5,1/5)

        def norm(val):
            t = (val + 3) / 6          # range 0..1 when val in [-3,3]
            return max(0, min(1, t))   # clamp
    
        r = norm(self.x)
        g = norm(self.y)
        b = norm(self.z)

        self.color = color.rgb(r, g, b)


camera = EditorCamera()


boids = [Boid() for _ in range(10)]

Entity(model='plane', scale=10, color=color.gray, texture='white_cube',)

app.run()