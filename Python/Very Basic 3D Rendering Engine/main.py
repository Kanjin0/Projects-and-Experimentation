import pygame
from typing import NamedTuple
from math import cos, sin, pi, sqrt
import engine_config
from math_utils import *
from renderer import *
import model_loader

try:
    solid, faces = model_loader.load_obj("cube.obj")
except FileNotFoundError:
    print("Model not found – loading default hexagonal prism.")
    solid, faces = model_loader.load_hexagonal_prism()


solid , faces = model_loader.load_hexagonal_prism()

# Preparation and Designation of constants
pygame.init()

window = engine_config.window
pygame.display.set_caption(engine_config.window_name)

clock = pygame.time.Clock()

def gameloop():

    loop = True
    deltaTime = 1/engine_config.FPS
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
                    engine_config.CAMERA_THETA += -dx * 0.005 # move object sideways
                    engine_config.CAMERA_PHI += -dy * 0.005 # move object up and down
            elif event.type == pygame.MOUSEWHEEL:
                engine_config.FOCAL_LENGTH += event.y * 75
                engine_config.FOCAL_LENGTH = max(100, min(2000, engine_config.FOCAL_LENGTH))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    engine_config.BACK_CULLING = not engine_config.BACK_CULLING
                elif event.key == pygame.K_v:
                    engine_config.DRAW_VERTEXES = not engine_config.DRAW_VERTEXES
                elif event.key == pygame.K_e:
                    engine_config.DRAW_EDGES = not engine_config.DRAW_EDGES
                elif event.key == pygame.K_f:
                    engine_config.DRAW_FACES = not engine_config.DRAW_FACES

        #Draw background (mostly for distinction of what is what)
        window.fill(engine_config.BACKGROUND_COLOR)

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
        eye_x = engine_config.CAMERA_R * cos(engine_config.CAMERA_PHI) * sin(engine_config.CAMERA_THETA)
        eye_y = engine_config.CAMERA_R * sin(engine_config.CAMERA_PHI)
        eye_z = engine_config.CAMERA_R * cos(engine_config.CAMERA_PHI) * cos(engine_config.CAMERA_THETA)
        #Define where is forward pointed to (from eye to target, target = (0,0,0))
        fx , fy, fz = -eye_x, -eye_y, -eye_z
        len_fwd = sqrt(fx*fx + fy*fy + fz*fz)
        if len_fwd > 1e-10:
            fx /= len_fwd; fy /= len_fwd; fz /= len_fwd
        else:
            fx, fy, fz = 0, 0, 1   # fallback

        # Compute right = up × forward
        rx = cos(engine_config.CAMERA_THETA)
        ry = 0.0
        rz = -sin(engine_config.CAMERA_THETA)
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
                screen_x = engine_config.FOCAL_LENGTH * x_cam / z_cam + engine_config.window_width / 2
                screen_y = -engine_config.FOCAL_LENGTH * y_cam / z_cam + engine_config.window_height / 2
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
            if engine_config.BACK_CULLING:
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
        if engine_config.BACK_CULLING and (engine_config.DRAW_EDGES or engine_config.DRAW_VERTEXES):
            for _, face_idxs in face_depth:
                for idx in face_idxs:
                    visible_verts.add(idx)
                for i in range (len(face_idxs)):
                    v1 = face_idxs[i]
                    v2 = face_idxs[(i+1) % len(face_idxs)]
                    edg = tuple(sorted((v1,v2)))
                    visible_edges.add(edg)



        #Now that all the math has been done, we can simply draw everything according to the previous sortings
        if engine_config.DRAW_FACES:
            for _, face_idxs in face_depth:
                face_points = [projected_points[i] for i in face_idxs]
                face(face_points)
                
        if engine_config.DRAW_EDGES:
            for edge in lines:
                if engine_config.BACK_CULLING:
                    if edge in visible_edges:
                        p1 = projected_points[edge[0]]
                        p2 = projected_points[edge[1]]
                        if p1 is not None and p2 is not None: line(p1,p2)
                else:
                    p1 = projected_points[edge[0]]
                    p2 = projected_points[edge[1]]
                    if p1 is not None and p2 is not None: line(p1,p2)
                    

        if engine_config.DRAW_VERTEXES:
            if engine_config.BACK_CULLING:
                for i, pt in enumerate(projected_points):
                    if i in visible_verts and pt is not None:
                        point(pt)
            else:
                for pt in projected_points:
                    if pt is not None: point(pt)
        
        pygame.display.update()
        clock.tick(engine_config.FPS)
    clock.tick(engine_config.FPS)
    pygame.quit()

gameloop()