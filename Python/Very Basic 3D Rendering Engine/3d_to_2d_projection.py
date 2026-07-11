import pygame
from typing import NamedTuple
from math import cos, sin, pi, sqrt

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
BACK_CULLING = True
DRAW_VERTEXES = True
DRAW_EDGES = True
DRAW_FACES = True
VERTEX_COLOR = (40,144,69)
EDGE_COLOR = (236,172,50)
FACE_COLOR = (96,47,189)

# Camera
CAMERA_R = 4.0
CAMERA_THETA = 0.0          # radians
CAMERA_PHI = pi / 4         # 45° elevation
FOCAL_LENGTH = 500.0        # pixels

#Lighting

class Point2D(NamedTuple):
    x: float
    y: float

class Point3D(NamedTuple):
    x: float
    y: float
    z: float

# ---------- HEXAGONAL PRISM ----------
r = .7        # radius of the hexagon
h = .7        # half‑height (y goes from -h to +h)

solid = []

# Top face (y = +h)
for i in range(6):
    angle = 2 * pi * i / 6
    solid.append(Point3D(r * cos(angle), h, r * sin(angle)))

# Bottom face (y = -h)
for i in range(6):
    angle = 2 * pi * i / 6
    solid.append(Point3D(r * cos(angle), -h, r * sin(angle)))

# Vertices 0–5 = top, 6–11 = bottom
faces = [
    [5, 4, 3, 2, 1, 0],          # Top face (fixed: outward +Y)
    [6, 7, 8, 9, 10, 11],        # Bottom face (unchanged: outward -Y)
    [0, 1, 7, 6],                # Side 1
    [1, 2, 8, 7],                # Side 2
    [2, 3, 9, 8],                # Side 3
    [3, 4, 10, 9],               # Side 4
    [4, 5, 11, 10],              # Side 5
    [5, 0, 6, 11]                # Side 6
]

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
    global BACK_CULLING, DRAW_VERTEXES, DRAW_EDGES, DRAW_FACES
    global CAMERA_R, CAMERA_THETA, CAMERA_PHI, FOCAL_LENGTH
    loop = True
    deltaTime = 1/FPS
    deltaZ = 1
    theta = pi*deltaTime/2
    angle = 0
    lines = build_wireframe_from_faces(faces)

    while loop:
        angle = angle + theta

        '''#Some back and forth Motion
        if cos(angle/1.1) > 0:
            deltaZ = min(deltaZ + deltaTime/2,3)
        else:
            deltaZ = max(deltaZ - deltaTime/2,-3)'''
        
        #Handle events (might implement drawing a solid by clicking to add vertexes)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # left button held
                    dx, dy = event.rel
                    CAMERA_THETA += -dx * 0.005 # move object sideways
                    CAMERA_PHI += -dy * 0.005 # move object up and down
            elif event.type == pygame.MOUSEWHEEL:
                FOCAL_LENGTH += event.y * 75
                FOCAL_LENGTH = max(100, min(2000, FOCAL_LENGTH))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    BACK_CULLING = not BACK_CULLING
                elif event.key == pygame.K_v:
                    DRAW_VERTEXES = not DRAW_VERTEXES
                elif event.key == pygame.K_e:
                    DRAW_EDGES = not DRAW_EDGES
                elif event.key == pygame.K_f:
                    DRAW_FACES = not DRAW_FACES

        #Draw background (mostly for distinction of what is what)
        window.fill(BACKGROUND_COLOR)

        #Draw Everything Else (make all transformations here so they're "less expensive" and then just use the points on projected points on the other drawing phases)
        transformed_3d = [] # Need this one because projection squashes z so we can't do z-sorting with the points of the list above
        
        #Apply Transformations to all points (need to be stacked, both for translation and rotation)
        for p in solid:
            rotations = rotation(
                rotation(
                    Point3D(p.x, p.y, p.z),1,0),2,
                    0)
            
            transformations = rotations; '''translation(rotations,2,deltaZ)'''
            transformed_3d.append(transformations)

            #We stopped defining the positions of the points projected into the screen here because now it'll be need to also take into accound the position of the camera
        
        #Camera Setup
        #Camera Position
        eye_x = CAMERA_R * cos(CAMERA_PHI) * sin(CAMERA_THETA)
        eye_y = CAMERA_R * sin(CAMERA_PHI)
        eye_z = CAMERA_R * cos(CAMERA_PHI) * cos(CAMERA_THETA)
        #Define where is forward pointed to (from eye to target, target = (0,0,0))
        fx , fy, fz = -eye_x, -eye_y, -eye_z
        len_fwd = sqrt(fx*fx + fy*fy + fz*fz)
        if len_fwd > 1e-10:
            fx /= len_fwd; fy /= len_fwd; fz /= len_fwd
        else:
            fx, fy, fz = 0, 0, 1   # fallback

        # Compute right = up × forward
        rx = cos(CAMERA_THETA)
        ry = 0.0
        rz = -sin(CAMERA_THETA)
        len_r = sqrt(rx*rx + ry*ry + rz*rz)
        if len_r > 1e-10:
            rx /= len_r; ry /= len_r; rz /= len_r
        else:
            rx, ry, rz = 1.0, 0.0, 0.0   # fallback (should never happen)

        # Compute up = forward × right (right-handed basis)
        upx = fy * rz - fz * ry
        upy = fz * rx - fx * rz
        upz = fx * ry - fy * rx
        len_up = sqrt(upx*upx + upy*upy + upz*upz)
        if len_up > 1e-10:
            upx /= len_up; upy /= len_up; upz /= len_up
        else:
            upx, upy, upz = 0.0, 1.0, 0.0   # fallback (unlikely)

        cam_space = []
        projected_points = []

        for world in transformed_3d:
            Vx = world.x - eye_x
            Vy = world.y - eye_y
            Vz = world.z - eye_z

            x_cam = Vx * rx + Vy * ry + Vz * rz
            y_cam = Vx * upx + Vy * upy + Vz * upz
            z_cam = Vx * fx + Vy * fy + Vz * fz
            cam_space.append(Point3D(x_cam, y_cam, z_cam))

            if z_cam > 1e-6:
                screen_x = FOCAL_LENGTH * x_cam / z_cam + window_width / 2
                screen_y = -FOCAL_LENGTH * y_cam / z_cam + window_height / 2
                projected_points.append(Point2D(screen_x, screen_y))
            else:
                projected_points.append(None)

        #Calculate the avg z of each of the faces and put it into a list to choose from later
        face_depth = []
        for face_idxs in faces:
            all_visible = True
            for i in face_idxs:
                if projected_points[i] is None:
                    all_visible = False
                    break
            if not all_visible: continue
            if BACK_CULLING:
                #These 3 points are used to calculated the normal of each face, making it possible to apply back-culling to them.
                v0 = cam_space[face_idxs[0]]
                v1 = cam_space[face_idxs[1]]
                v2 = cam_space[face_idxs[2]]

                a,b,c = calculate_face_normal(v0,v1,v2)

                if c < -1e-5:
                    avg_z = sum(cam_space[i].z for i in face_idxs) / len(face_idxs)
                    face_depth.append((avg_z,face_idxs))
            else:
                avg_z = sum(cam_space[i].z for i in face_idxs) / len(face_idxs)
                face_depth.append((avg_z,face_idxs))

        face_depth.sort(key= lambda x: x[0], reverse= True) #We use reverse because: our model has z increasing into the screen so larger z means farther into the back
                                                            #Therefore, we those faces with larger z in the front of the list so when we draw the ones with smaller z, they get drawn over the 1st ones
        
        visible_verts = set()
        visible_edges = set()
        if BACK_CULLING and (DRAW_EDGES or DRAW_VERTEXES):
            for _, face_idxs in face_depth:
                for idx in face_idxs:
                    visible_verts.add(idx)
                for i in range (len(face_idxs)):
                    v1 = face_idxs[i]
                    v2 = face_idxs[(i+1) % len(face_idxs)]
                    edg = tuple(sorted((v1,v2)))
                    visible_edges.add(edg)



        #Now that all the math has been done, we can simply draw everything according to the previous sortings
        if DRAW_FACES:
            for _, face_idxs in face_depth:
                face_points = [projected_points[i] for i in face_idxs]
                face(face_points)
                
        if DRAW_EDGES:
            for edge in lines:
                if BACK_CULLING:
                    if edge in visible_edges:
                        p1 = projected_points[edge[0]]
                        p2 = projected_points[edge[1]]
                        if p1 is not None and p2 is not None: line(p1,p2)
                else:
                    p1 = projected_points[edge[0]]
                    p2 = projected_points[edge[1]]
                    if p1 is not None and p2 is not None: line(p1,p2)
                    

        if DRAW_VERTEXES:
            if BACK_CULLING:
                for i, pt in enumerate(projected_points):
                    if i in visible_verts and pt is not None:
                        point(pt)
            else:
                for pt in projected_points:
                    if pt is not None: point(pt)
        
        pygame.display.update()
        clock.tick(FPS)
    clock.tick(FPS)
    pygame.quit()

gameloop()