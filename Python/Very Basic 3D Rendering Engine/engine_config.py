from math import pi
import pygame


#Window
window_name = "3D in 2D projection"
window_height = 900
window_width = 900
BACKGROUND_COLOR = (80, 80, 80)

window = pygame.display.set_mode((window_width,window_height))

# FrameRate
FPS = 60

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