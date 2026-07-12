import os
import pygame
from math import cos, sin, sqrt
from array import array
import engine_config
from math_utils import *
from renderer import *
import model_loader

# ---- Load model ----
try:
    solid, faces, solid_normals = model_loader.load_obj("sphere.obj", scale_to_fit=1.5)
except FileNotFoundError:
    print("Model not found – loading default hexagonal prism.")
    solid, faces = model_loader.load_hexagonal_prism()
    solid_normals = compute_vertex_normals(solid, faces)

'''solid, faces = model_loader.load_hexagonal_prism()
solid_normals = compute_vertex_normals(solid, faces)'''

# ---- Safety: ensure normals are valid ----
if len(solid_normals) != len(solid):
    print(f"Warning: normals count ({len(solid_normals)}) != vertices ({len(solid)}) – recomputing.")
    solid_normals = compute_vertex_normals(solid, faces)

if any(n is None for n in solid_normals):
    print("Warning: some normals are None – recomputing.")
    solid_normals = compute_vertex_normals(solid, faces)

if any(n is None for n in solid_normals):
    print("Falling back to default normals (0,1,0).")
    solid_normals = [Point3D(0, 1, 0) for _ in solid]

print(f"Loaded {len(solid)} vertices, {len(faces)} faces, {len(solid_normals)} normals.")
print(f"First normal: {solid_normals[0] if solid_normals else 'None'}")

# ---- Pre‑compute triangles ----
triangles = precompute_triangles(solid, faces)
print(f"Pre‑computed {len(triangles)} triangles.")

# Build wireframe edges from the ORIGINAL faces (not triangles)
lines = build_wireframe_from_faces(faces)

# ---- Pygame setup ----
pygame.init()
window = engine_config.window
pygame.display.set_caption(engine_config.window_name)
clock = pygame.time.Clock()

def gameloop():
    global engine_config

    loop = True
    deltaTime = 1 / engine_config.FPS
    theta = pi * deltaTime / 2

    angle_x = pi      # upright
    angle_y = 0.0
    angle_z = 0.0

    while loop:
        # (Optional) auto‑rotation
        # angle_y += theta * 0.5

        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    dx, dy = event.rel
                    angle_y -= dx * 0.005
                    angle_x += dy * 0.005
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
                elif event.key == pygame.K_l:  # cycle shading (None ↔ Phong)
                    if engine_config.SHADING_MODE == engine_config.SHADING_NONE:
                        engine_config.SHADING_MODE = engine_config.SHADING_PHONG
                    else:
                        engine_config.SHADING_MODE = engine_config.SHADING_NONE
                    print(f"Shading mode: {'None' if engine_config.SHADING_MODE == engine_config.SHADING_NONE else 'Phong'}")

        # ---- Clear ----
        window.fill(engine_config.BACKGROUND_COLOR)

        # ---- Transform vertices & normals ----
        transformed_3d = []
        transformed_normals = []
        for i, p in enumerate(solid):
            rot1 = rotation(Point3D(p.x, p.y, p.z), 0, angle_x)
            rot2 = rotation(rot1, 1, angle_y)
            rot3 = rotation(rot2, 2, angle_z)
            transformed_3d.append(rot3)

            n = solid_normals[i]
            nr1 = rotation(Point3D(n.x, n.y, n.z), 0, angle_x)
            nr2 = rotation(nr1, 1, angle_y)
            nr3 = rotation(nr2, 2, angle_z)
            transformed_normals.append(nr3)

        # ---- Camera & Projection ----
        eye_x = engine_config.CAMERA_R * cos(engine_config.CAMERA_PHI) * sin(engine_config.CAMERA_THETA)
        eye_y = engine_config.CAMERA_R * sin(engine_config.CAMERA_PHI)
        eye_z = engine_config.CAMERA_R * cos(engine_config.CAMERA_PHI) * cos(engine_config.CAMERA_THETA)

        fx, fy, fz = -eye_x, -eye_y, -eye_z
        len_fwd = sqrt(fx*fx + fy*fy + fz*fz)
        if len_fwd > 1e-10:
            fx /= len_fwd; fy /= len_fwd; fz /= len_fwd
        else:
            fx, fy, fz = 0, 0, 1

        rx = cos(engine_config.CAMERA_THETA)
        ry = 0.0
        rz = -sin(engine_config.CAMERA_THETA)
        len_r = sqrt(rx*rx + ry*ry + rz*rz)
        if len_r > 1e-10:
            rx /= len_r; ry /= len_r; rz /= len_r
        else:
            rx, ry, rz = 1.0, 0.0, 0.0

        upx = fy * rz - fz * ry
        upy = fz * rx - fx * rz
        upz = fx * ry - fy * rx
        len_up = sqrt(upx*upx + upy*upy + upz*upz)
        if len_up > 1e-10:
            upx /= len_up; upy /= len_up; upz /= len_up
        else:
            upx, upy, upz = 0.0, 1.0, 0.0

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

            if z_cam > 1e-9:
                screen_x = engine_config.FOCAL_LENGTH * x_cam / z_cam + engine_config.window_width / 2
                screen_y = -engine_config.FOCAL_LENGTH * y_cam / z_cam + engine_config.window_height / 2
                projected_points.append(Point2D(screen_x, screen_y))
            else:
                projected_points.append(None)

        # ---- Visible edges & vertices ----
        visible_verts = set()
        visible_edges = set()
        if engine_config.BACK_CULLING and (engine_config.DRAW_EDGES or engine_config.DRAW_VERTEXES):
            for face_idxs in faces:
                all_visible = True
                for i in face_idxs:
                    if projected_points[i] is None:
                        all_visible = False
                        break
                if not all_visible:
                    continue
                v0 = cam_space[face_idxs[0]]
                v1 = cam_space[face_idxs[1]]
                v2 = cam_space[face_idxs[2]]
                a, b, c = calculate_face_normal(v0, v1, v2)
                if c < -1e-5:
                    for idx in face_idxs:
                        visible_verts.add(idx)
                    for i in range(len(face_idxs)):
                        v1 = face_idxs[i]
                        v2 = face_idxs[(i + 1) % len(face_idxs)]
                        visible_edges.add(tuple(sorted((v1, v2))))

        # ---- Draw faces ----
        if engine_config.DRAW_FACES:
            # Reset Z‑buffer
            engine_config.Z_BUFFER[:] = array('f', [float('inf')]) * (engine_config.window_width * engine_config.window_height)

            pixels = pygame.PixelArray(window)

            for tri in triangles:
                # Visibility
                all_visible = True
                for idx in tri:
                    if projected_points[idx] is None:
                        all_visible = False
                        break
                if not all_visible:
                    continue

                # Back‑face culling
                if engine_config.BACK_CULLING:
                    v0 = cam_space[tri[0]]
                    v1 = cam_space[tri[1]]
                    v2 = cam_space[tri[2]]
                    a, b, c = calculate_face_normal(v0, v1, v2)
                    if c >= -1e-5:
                        continue

                p0 = projected_points[tri[0]]
                p1 = projected_points[tri[1]]
                p2 = projected_points[tri[2]]
                z0 = cam_space[tri[0]].z
                z1 = cam_space[tri[1]].z
                z2 = cam_space[tri[2]].z

                # Prepare normals only if Phong mode is active
                if engine_config.SHADING_MODE == engine_config.SHADING_PHONG:
                    n0 = transformed_normals[tri[0]]
                    n1 = transformed_normals[tri[1]]
                    n2 = transformed_normals[tri[2]]
                else:
                    n0 = n1 = n2 = None

                rasterize_triangle_tiled_lighting(p0, p1, p2, z0, z1, z2, pixels,
                                                  n0=n0, n1=n1, n2=n2,
                                                  base_color=engine_config.FACE_COLOR)

            del pixels

        # ---- Draw edges & vertices (unchanged) ----
        if engine_config.DRAW_EDGES:
            for edge in lines:
                if engine_config.BACK_CULLING and edge not in visible_edges:
                    continue
                p1 = projected_points[edge[0]]
                p2 = projected_points[edge[1]]
                if p1 is not None and p2 is not None:
                    line(p1, p2)

        if engine_config.DRAW_VERTEXES:
            if engine_config.BACK_CULLING:
                for i, pt in enumerate(projected_points):
                    if i in visible_verts and pt is not None:
                        point(pt)
            else:
                for pt in projected_points:
                    if pt is not None:
                        point(pt)

        pygame.display.update()
        clock.tick(engine_config.FPS)

    pygame.quit()

if __name__ == "__main__":
    gameloop()