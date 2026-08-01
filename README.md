# Personal Project Repository

Welcome to my repository of experiments, small engines, and learning projects.

It is organized by **programming language** to keep things tidy as I explore various areas of software development. Each project lives in its own folder under the appropriate language directory.

---

## 📁 Current Folder Structure
/
├── README.md
├── Python/ # All Python-based projects
│ └── Very Basic 3D Rendering Engine/
│ │ ├── main.py
│ │ ├── renderer.py
│ │ ├── math_utils.py
│ │ ├── engine_config.py
│ │ ├── model_loader.py
│ │ ├── materials.py
│ │ ├── Models/ # .obj and .mtl files
│ │ ├── rasterizer.c # C optimised rasterizer
│ │ └── rasterizer.dll # (compiled)


> Each language folder contains only projects written predominantly in that language. A project may include components in other languages (e.g., a C extension in a Python project) – the folder is chosen by the primary language.

---

## 🚀 Current Projects

### 🧊 Very Basic 3D Rendering Engine

A **software 3D renderer** written in Python with a **C-optimised rasterizer** for performance.  
It loads standard `.obj` files with materials (`.mtl`), applies **Phong shading**, supports **Z‑buffering**, **back‑face culling**, and **per‑face materials**.  
The engine is entirely CPU‑based – no GPU required – and demonstrates how 3D graphics works under the hood.

**Key features:**
- OBJ file loader (with material support)
- Perspective projection with camera orbit
- Tile‑based rasterization (C and Python)
- Z‑buffer for perfect occlusion
- Phong lighting (diffuse + specular) with material properties
- Keyboard/mouse controls (rotate, zoom, toggle features)
- Hybrid architecture: Python for flexibility, C for speed

**Performance:**  
For high‑poly models (e.g., 35k triangles), the C rasterizer delivers **about 25 FPS** on the tested CPU (AMD Ryzen 7 w/ Radeon 780M Graphics), while the Python fallback handles simpler scenes.

---

## 🔧 Dependencies

### Python
- **Python 3.8+**
- **Pygame** – windowing and input
- **NumPy** – efficient array handling for C binding

Install them with:
```bash
pip install pygame numpy