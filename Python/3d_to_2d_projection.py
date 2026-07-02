import pygame
from typing import NamedTuple
from math import cos, sin, pi

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

cubeSize = 1
half = cubeSize/2

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

lines = [   
    (0,1),
    (1,2),
    (2,3),
    (3,0),

    (4,5),
    (5,6),
    (6,7),
    (7,4),

    (0,4),
    (1,5),
    (2,6),
    (3,7),

]

#Draw rectangle with center at an x,y coord accounting for its size (so it's correctly placed there instead of placing the top right corner there) 

def point(point:Point2D):
    size = 10
    pygame.draw.rect(window, USE_COLOR,(point.x - size/2, point.y- size/2,size,size))

def line(point1:Point2D, point2:Point2D):
    size = 2
    pygame.draw.line(window,USE_COLOR, (point1.x, point1.y), (point2.x, point2.y),size)

def screenCoord(point:Point2D):
    return Point2D((point.x + 1)*window_width/2, (-point.y + 1)*window_height/2)

def projection(point:Point3D):
    return Point2D(point.x/point.z, point.y/point.z)

def translation(point:Point3D, deltaZ):
    return Point3D(point.x,point.y,point.z + deltaZ)

def rotation_zAxis(point:Point3D, angle):
    return Point3D(point.x*cos(angle) - point.y*sin(angle),point.x*sin(angle)+ point.y*cos(angle),point.z)

def rotation_yAxis(point:Point3D, angle):
    return Point3D(point.x*cos(angle) + point.z*sin(angle),point.y, -point.x*sin(angle) + point.z*cos(angle))

def rotation_xAxis(point:Point3D, angle):
    return Point3D(point.x,point.y*cos(angle) - point.z*sin(angle),point.y*sin(angle) + point.z*cos(angle))


def gameloop():
    loop = True
    deltaTime = 1/FPS
    deltaZ = 0
    theta = pi*deltaTime/2
    angle = 0

    while loop:
        deltaZ = min(deltaZ + deltaTime/2,2)
        angle = angle + theta
        
        #Handle events (might implement drawing a solid by clicking to add vertexes)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False

        #Draw background (mostly for distinction of what is what)
        window.fill(BACKGROUND_COLOR)

        #Draw Everything Else
        '''for p in solid:
            point(screenCoord(projection(translation(Point3D(p.x, p.y, p.z),deltaZ))))'''
        
        for idx1,idx2 in lines:
            p1 = solid[idx1]
            p2 = solid[idx2]
            
            rotations1 = rotation_zAxis(
                rotation_xAxis(
                    Point3D(p1.x, p1.y, p1.z),angle*0.5),
                    angle)
            rotations2 = rotation_zAxis(
                rotation_xAxis(
                    Point3D(p2.x, p2.y, p2.z),angle*0.5),
                    angle)
            point1 = screenCoord(projection(translation(rotations1,deltaZ)))
            point2 = screenCoord(projection(translation(rotations2,deltaZ)))

            line(point1,point2)

        pygame.display.update()
        clock.tick(FPS)
    clock.tick(FPS)
    pygame.quit()

gameloop()