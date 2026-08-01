#include <math.h>
#include <stdint.h>
#include <stdlib.h>

// compile with: gcc -shared -O3 -march=native -o rasterizer.dll rasterizer.c -lm

void rasterize_triangle_tiled_lighting_material(
    int num_triagles, 
    const float *vertices,
    const float *normals, 
    const int *indices,
    const float *mat_diffuse,
    const float *mat_specular,
    const float *mat_shininess, 
    int width, int height,
    float *z_buffer, unsigned char *framebuffer, 
    int shading_mode,
    float ambient, float light_dir[3], float spec_strength ){

        const int TILE = 32;
        const float EPS = -1e-6f;

        // Normalize the light direction just because yes
        float lx = light_dir[0], ly = light_dir[1], lz = light_dir[2];
        float len = sqrtf(lx*lx + ly*ly + lz*lz);
        if (len > 1e-10){
            lx /= len;
            ly /= len;
            lz /= len;
        }

        // View direction (simplified - camera just looks aling positive Z)
        const float vx = 0.0f, vy = 0.0f, vz = 1.0f;
        
        // Loop over triangles
        for(int tri = 0; tri < num_triagles; ++tri){
            int vertex_base = tri*9; // 9 = 3 vertices * 3 coord each
            int normals_base = tri*9;
            int idxs_base = tri*3;   // 3 vertex indices

            //Get vertex indices
            int i0 = indices[idxs_base];
            int i1 = indices[idxs_base + 1];
            int i2 = indices[idxs_base + 2];

            // Get screen‑space positions (x, y, depth) for each vertex
            // They are stored in the vertices array as: [x0, y0, depth0, x1, y1, depth1, x2, y2, depth2]
            const float *v0 = &vertices[vertex_base];
            const float *v1 = &vertices[vertex_base + 3];
            const float *v2 = &vertices[vertex_base + 6];


            float p0x = v0[0], p0y = v0[1], p0z = v0[2];
            float p1x = v1[0], p1y = v1[1], p1z = v1[2];
            float p2x = v2[0], p2y = v2[1], p2z = v2[2];

            // ---- Bounding box (clamped to screen) ----
            int min_x = (int) fmaxf(0.0f, fminf(p0x,fminf(p1x,p2x)));
            int min_y = (int) fmaxf(0.0f, fminf(p0y, fminf(p1y,p2y)));
            int max_x = (int) fminf((float)(width - 1),fmaxf(p0x,fmaxf(p1x,p2x)));
            int max_y = (int) fminf((float)(height - 1),fmaxf(p0y,fmaxf(p1y,p2y)));
        
            if( min_x > max_x || min_y > max_y) continue;

            // ---- Barycentric constants ----
            float v0x = p1x - p0x , v0y = p1y - p0y;
            float v1x = p2x - p0x , v1y = p2y - p0y;
            float denom = v0x * v1y - v1x*v0y;
            if(fabsf(denom) < 1e-10f) continue;
            float inv_denom = 1.0f / denom;

            // ---- Tile Range ----
            int tx_start = min_x / TILE;
            int tx_end = max_x / TILE;
            int ty_start = min_y / TILE;
            int ty_end = max_y / TILE;

            // ---- Mat Properties (per triangle) ----
            const float *diff = &mat_diffuse[tri * 3];
            const float *spec = &mat_specular[tri * 3];
            float shin = mat_shininess[tri];

            const float *n0 = (shading_mode == 1) ? &normals[normals_base]: NULL;
            const float *n1 = (shading_mode == 1) ? &normals[normals_base + 3]: NULL;
            const float *n2 = (shading_mode == 1) ? &normals[normals_base + 6]: NULL;
            
            // ---- Tile Loops ----
            for(int ty = ty_start; ty <= ty_end; ++ty){
                int tile_y = ty * TILE;
                for(int tx = tx_start; tx <= tx_end; tx++){
                    int tile_x = tx * TILE;
                    
                    // Quick reject if the tule is outside the triangles' bounding box
                    if(tile_x > max_x || tile_x + TILE - 1 < min_x) continue;
                    if(tile_y > max_y || tile_y + TILE - 1 < min_y) continue;
                
                    for(int dy = 0; dy < TILE; ++dy){
                        int y = tile_y + dy;
                        if (y > max_y) break;
                        int row_offset = y * width;
                        for(int dx = 0; dx < TILE; ++dx){
                            int x = tile_x + dx;
                            if (x > max_x) break;

                            float v2x = (float)x - p0x, v2y = (float)y - p0y;
                            float u = (v2x * v1y - v1x * v2y) * inv_denom;
                            float v = (v0x * v2y - v2x * v0y) * inv_denom;
                            float w = 1.0f - u - v;

                            if (u >= -EPS && v >= -EPS && w >= -EPS){

                                // Clamping to avoid negative values
                                if (u < 0.0f) u = 0.0f;
                                if (v < 0.0f) v = 0.0f;
                                if (w < 0.0f) w = 0.0f;

                                // Interpolation to get depth
                                float depth = u * p0z + v * p1z + w * p2z;
                                int idx = row_offset + x;

                                if (depth < z_buffer[idx]){
                                    z_buffer[idx] = depth;

                                    // ---- Shading ----

                                    if (shading_mode == 0){

                                        // Flat shading
                                        int r = (int)(diff[0] * 255.0f);
                                        int g = (int)(diff[1] * 255.0f);
                                        int b = (int)(diff[2] * 255.0f);

                                        // Clamp the values
                                        if (r > 255) r = 255;
                                        if (g > 255) g = 255;
                                        if (b > 255) b = 255;

                                        int pos = idx * 3;

                                        framebuffer[pos] = (unsigned char)r;
                                        framebuffer[pos + 1] = (unsigned char)g;
                                        framebuffer[pos + 2] = (unsigned char)b;
                                    }
                                    else {
                                        // Phong Shading - interpolate normal
                                        float nx = u* n0[0] + v* n1[0] + w* n2[0];
                                        float ny = u* n0[1] + v* n1[1] + w* n2[1];
                                        float nz = u* n0[2] + v* n1[2] + w* n2[2];
                                        float n_len = sqrtf(nx*nx + ny*ny + nz*nz);
                                        if (n_len > 1e-10f){
                                            nx /= n_len; ny /= n_len; nz /= n_len;
                                        }
                                        else{
                                            nx = 0.0f; ny = 0.0f; nz = 0.0f;
                                        }

                                        // Diffuse
                                        float diff_val = nx*lx + ny*ly + nz*lz;
                                        if (diff_val < 0.0f) diff_val = 0.0f;
                                        float intensity = ambient + (1.0f - ambient) * diff_val;

                                        //Specular
                                        float hx = lx + vx, hy = ly + vy, hz = lz * vz;
                                        float h_len = sqrtf(hx*hx + hy*hy + hz*hz);
                                        float spec_val = 0.0f;

                                        if (h_len > 1e-10f){
                                            hx /= h_len; hy /= h_len; hz /= h_len;
                                            float dot = nx*hx + ny*hy + nz*hz;

                                            if (dot < 0.0f) dot = 0.0f;
                                            
                                            spec_val = powf(dot, shin);
                                            intensity += spec_strength * spec_val;

                                            if (intensity > 1.0f) intensity = 1.0f;
                                        }

                                        float r = diff[0] * intensity + spec[0] * spec_val*spec_strength;
                                        float g = diff[1] * intensity + spec[1] * spec_val*spec_strength;
                                        float b = diff[2] * intensity + spec[2] * spec_val*spec_strength;
                                        
                                        int ri = (int)(r * 255.0f);
                                        int gi = (int)(g * 255.0f);
                                        int bi = (int)(b * 255.0f);
                                        
                                        if (ri > 255) ri = 255;
                                        if (gi > 255) gi = 255;
                                        if (bi > 255) bi = 255;
                                        
                                        int pos = idx * 3;
                                        
                                        framebuffer[pos] = (unsigned char)ri;
                                        framebuffer[pos + 1] = (unsigned char)gi;
                                        framebuffer[pos + 2] = (unsigned char)bi;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }


}