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

faces = [
    (0,1,2,3), # Back Face (z = half + starting_plane) - Farthest from camera/user (at/close to z = 0) (Normal: +Z) - Away from camera
    (5,4,7,6), # Front Face (z = -half + starting_plane) - Farthest from camera/user (Normal: -Z) - Towards camera

    (1,5,6,2), # Left Face (x = -half) (Normal: -X)
    (3,7,4,0), # Right Face (x = +half) (Normal: +X)

    (4,5,1,0), # Top Face (y = +half) (Normal: +Y)
    (3,2,6,7), # Bottom Face (y = -half) (Normal: -Y)
]

#Draw rectangle with center at an x,y coord accounting for its size (so it's correctly placed there instead of placing the top right corner there) 
def point(point:Point2D):
    size = 10
    pygame.draw.rect(window, USE_COLOR,(point.x - size/2, point.y- size/2,size,size))

#Draw a line conecting both points specified
def line(point1:Point2D, point2:Point2D):
    size = 2
    pygame.draw.line(window,USE_COLOR, (point1.x, point1.y), (point2.x, point2.y),size)

def build_wireframe_from_faces(faces:list):
    edges = set()
    for face in faces:
        for i in range(len(face)):
            v1 = face[i]
            v2 = face[(i+1) % len(face)]

            edge = tuple(sorted((v1,v2)))
            edges.add(edge)
    return list(edges)

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


def gameloop():
    loop = True
    deltaTime = 1/FPS
    deltaZ = 2
    theta = pi*deltaTime/2
    angle = 0
    lines = build_wireframe_from_faces(faces)

    while loop:
        angle = angle + theta

        #Some back and Forth Motion
        if cos(angle/1.1) > 0:
            deltaZ = min(deltaZ + deltaTime/2,3)
        else:
            deltaZ = max(deltaZ - deltaTime/2,-3)
        
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
            
            #Apply Transformations (need to be stacked, both for translation and rotation)
            rotations1 = rotation(
                rotation(
                    Point3D(p1.x, p1.y, p1.z),1,angle),2,
                    angle)
            rotations2 = rotation(
                rotation(
                    Point3D(p2.x, p2.y, p2.z),1,angle),2,
                    angle)

            transformations1 = translation(rotations1,2,deltaZ)
            transformations2 = translation(rotations2,2,deltaZ)

            #Define their coordenates in the screen
            point1 = screenCoord(projection(transformations1))
            point2 = screenCoord(projection(transformations2))


            line(point1,point2)

        for face in faces:
            pass

        pygame.display.update()
        clock.tick(FPS)
    clock.tick(FPS)
    pygame.quit()

gameloop()