import pygame
from engine_config import VERTEX_COLOR,EDGE_COLOR, FACE_COLOR, DRAW_FACES, window
from math_utils import Point2D


#Draw rectangle with center at an x,y coord accounting for its size (so it's correctly placed there instead of placing the top right corner there) 
def point(point:Point2D):
    size = 10
    pygame.draw.rect(window, VERTEX_COLOR,(point.x - size/2, point.y- size/2,size,size))

#Draw a line conecting both points specified
def line(point1:Point2D, point2:Point2D):
    size = 2
    if DRAW_FACES: size = 5
    pygame.draw.line(window,EDGE_COLOR, (point1.x, point1.y), (point2.x, point2.y),size) 
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