import pygame
from typing import NamedTuple
from math import cos, sin, pi

# Preparation and Designation of constants
pygame.init()

#Window
window_name = "3D in 2D projection"
window_height = 900
window_width = 900
BACKGROUND_COLOR = (80, 80, 80)
window = pygame.display.set_mode((window_width,window_height))
pygame.display.set_caption(window_name)

# FrameRate
FPS = 60
clock = pygame.time.Clock()

#Objects Drawn
DRAW_VERTEXES = True
DRAW_EDGES = True
DRAW_FACES = True
USE_COLOR = (0,255,50)
FACE_COLOR = (255, 0, 205)

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
    if DRAW_FACES: size = 7
    pygame.draw.line(window,USE_COLOR, (point1.x, point1.y), (point2.x, point2.y),size)

#Draw a face of the model conecting all points specified
def face(points:list):
    pygame.draw.polygon(window,FACE_COLOR,points)

#Build a list of tuples representing edges from pre-defined faces
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

        #Some back and forth Motion
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

        #Draw Everything Else (make all transformations here so they're "less expensive" and then just use the points on projected points on the other drawing phases)
        projected_points = []
        transformed_3d = [] # Need this one because projection squashes z so we can't do z-sorting with the points of the list above
        
        #Apply Transformations to all points (need to be stacked, both for translation and rotation) (and maybe draw vertexes)
        for p in solid:
            rotations = rotation(
                rotation(
                    Point3D(p.x, p.y, p.z),1,angle),2,
                    angle)
            
            transformations = translation(rotations,2,deltaZ)
            transformed_3d.append(transformations)

            #Define their coordenates in the screen
            point1 = screenCoord(projection(transformations))

            projected_points.append(point1)

            if DRAW_VERTEXES: point(point1)
        
        #Calculate the avg z of each of the faces and put it into a list to choose from later
        face_depth = []
        for face_idxs in faces:
            avg_z = sum(transformed_3d[i].z for i in face_idxs) / len(face_idxs)
            face_depth.append((avg_z,face_idxs))

        face_depth.sort(key= lambda x: x[0], reverse= True) #We use reverse because: our model has z increasing into the screen so larger z means farther into the back
                                                            #Therefore, we those faces with larger z in the front of the list so when we draw the ones with smaller z, they get drawn over the 1st ones
        
        #Now that all the math has been done, we can simply draw everything according to the previous sortings
        if DRAW_FACES:
            for avg_z, face_idxs in face_depth:
                face_points = [projected_points[i] for i in face_idxs]
                face(face_points)
                
        if DRAW_EDGES:
            for edge in lines:
                p1 = projected_points[edge[0]]
                p2 = projected_points[edge[1]]
                line(p1,p2)

        
        pygame.display.update()
        clock.tick(FPS)
    clock.tick(FPS)
    pygame.quit()

gameloop()