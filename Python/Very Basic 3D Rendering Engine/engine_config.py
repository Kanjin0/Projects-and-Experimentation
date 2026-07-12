from math import pi
import pygame
from array import array


#Window
window_name = "3D in 2D projection"
window_height = 600
window_width = 600
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

# Z-Buffering
Z_BUFFER = array('f', [float('inf')]) * (window_width * window_height)
Z_WIDTH = window_width
Z_HEIGHT = window_height

# Lighting
AMBIENT_STRENGTH = 0.1         # Ambient light (0.0 - 1.0)
LIGHT_DIR = (0.5, 0.8, 1.0)     # World-space direction (will be normalized)
SPECULAR_STRENGTH = 0.2         # Specular intensity
SHININESS = 16                  # Specular exponent

# Shading modes: 0 = None (solid color), 1 = Gouraud, 2 = Phong
SHADING_NONE = 0
SHADING_GOURAUD = 1
SHADING_PHONG = 2
SHADING_MODE = SHADING_PHONG