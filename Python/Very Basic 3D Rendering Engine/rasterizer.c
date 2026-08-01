#include <math.h>

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

        

}