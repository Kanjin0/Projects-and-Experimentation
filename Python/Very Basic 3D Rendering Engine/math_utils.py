from typing import NamedTuple
from engine_config import window_height, window_width

class Point2D(NamedTuple):
    x: float
    y: float

class Point3D(NamedTuple):
    x: float
    y: float
    z: float

#Calculate the direction the normal of the face belonging to the plane defined by the 3 parameter points is facing
def calculate_face_normal(p0:Point3D,p1:Point3D,p2:Point3D):

    #Direction vectors
    v0 = (p1.x - p0.x, p1.y - p0.y, p1.z - p0.z)
    v1 = (p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)

    #Cross Product
    a = v0[1]*v1[2] - v0[2]*v1[1]
    b = v0[2]*v1[0] - v0[0]*v1[2]
    c = v0[0]*v1[1] - v0[1]*v1[0]

    return (a,b,c)

#Transform normal cartesian coordinates from -1 ... 1 -> 0 ... 2 -> 0 ... 1 -> 0 ... window_width/height
def screenCoord(point:Point2D):
    return Point2D((point.x + 1)*window_width/2, (-point.y + 1)*window_height/2)