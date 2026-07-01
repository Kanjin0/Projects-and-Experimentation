import pygame
from typing import NamedTuple
# Preparation and Designation of constants
pygame.init()

FPS = 60
window_name = "3D in 2D projection"
window_height = 900
window_width = 900

BACKGROUND_COLOR = (80, 80, 80)
USE_COLOR = (0,255,50)

window = pygame.display.set_mode((window_width,window_height))
pygame.display.set_caption(window_name)

clock = pygame.time.Clock()

class Point2D(NamedTuple):
    x: float
    y: float

class Point3D(NamedTuple):
    x: float
    y: float
    z: float

def point(point:Point2D):
    size = 20
    pygame.draw.rect(window, USE_COLOR,(point.x - size/2, point.y- size/2,size,size))

def screenCoord(point:Point2D):
    return Point2D((point.x + 1)*window_width/2, (-point.y + 1)*window_height/2)

def projection(point:Point3D):
    return Point2D(point.x/point.z, point.y/point.z)

def gameloop():
    loop = True
    while loop:
        
        #Handle events (might implement drawing a solid by clicking to add vertexes)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False

        #Draw background (mostly for distinction of what is what)
        window.fill(BACKGROUND_COLOR)

        #Draw Everything Else
        point(screenCoord(projection(Point3D(0,0,1))))

        pygame.display.update()
        clock.tick(FPS)
    
    pygame.quit()

gameloop()