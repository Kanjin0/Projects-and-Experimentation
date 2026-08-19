#include <math.h>

// compile with: gcc -shared -O3 -march=native -o flock.dll flock.c -lm
// -march=native scans the CPU to optmize further so the .dll that's in the repo isn't for all machines. 
// You may need to remove it and compile it again or compile it with it so it's "shaped" to your current machine

void compute_flocking_forces(
    const float* positions,
    const float* velocities,
    const float* vision_radii,
    const float* separation_radii,
    float max_force,
    float max_speed,
    const int* neighbor_indices,
    const int* neighbor_offsets,
    int n,
    float* out_sep,
    float* out_ali,
    float* out_coh
){
    for (int i = 0; i < n; i++) {
        float px = positions[i*3];
        float py = positions[i*3 + 1];
        float pz = positions[i*3 + 2];
        float vx = velocities[i*3];
        float vy = velocities[i*3 + 1];
        float vz = velocities[i*3 + 2];

        float vision_radius = vision_radii[i];
        float separation_radius = separation_radii[i];

        float sep_steer_x = 0, sep_steer_y = 0, sep_steer_z = 0;
        float ali_steer_x = 0, ali_steer_y = 0, ali_steer_z = 0;
        float coh_steer_x = 0, coh_steer_y = 0, coh_steer_z = 0;

        int count_sep = 0;
        int count_ali = 0;
        int count_coh = 0;

        int start = neighbor_offsets[i];
        int end = neighbor_offsets[i + 1];

        for (int idx = start; idx < end; idx++) {
            int j = neighbor_indices[idx];
            if (j == i) continue;

            float dx = px - positions[j*3];
            float dy = py - positions[j*3 + 1];
            float dz = pz - positions[j*3 + 2];
            float d_sq = dx*dx + dy*dy + dz*dz;

            // Separation
            if (d_sq > 0 && d_sq < separation_radius * separation_radius) {
                float d = sqrtf(d_sq);
                float inv_d_sq = 1.0f / d_sq;
                float nx = dx / d;
                float ny = dy / d;
                float nz = dz / d;
                sep_steer_x += nx * inv_d_sq;
                sep_steer_y += ny * inv_d_sq;
                sep_steer_z += nz * inv_d_sq;
                count_sep++;
            }

            // Alignment & Cohesion
            if (d_sq < vision_radius * vision_radius) {
                ali_steer_x += velocities[j*3];
                ali_steer_y += velocities[j*3 + 1];
                ali_steer_z += velocities[j*3 + 2];
                count_ali++;

                coh_steer_x += positions[j*3];
                coh_steer_y += positions[j*3 + 1];
                coh_steer_z += positions[j*3 + 2];
                count_coh++;
            }
        }

        // Finalize separation
        if (count_sep > 0) {
            sep_steer_x /= count_sep;
            sep_steer_y /= count_sep;
            sep_steer_z /= count_sep;
            float len = sqrtf(sep_steer_x*sep_steer_x + sep_steer_y*sep_steer_y + sep_steer_z*sep_steer_z);
            if (len > 1e-6f) {
                sep_steer_x /= len; sep_steer_y /= len; sep_steer_z /= len;
                sep_steer_x *= max_speed;
                sep_steer_y *= max_speed;
                sep_steer_z *= max_speed;
                sep_steer_x -= vx;
                sep_steer_y -= vy;
                sep_steer_z -= vz;
                len = sqrtf(sep_steer_x*sep_steer_x + sep_steer_y*sep_steer_y + sep_steer_z*sep_steer_z);
                if (len > max_force) {
                    sep_steer_x *= max_force / len;
                    sep_steer_y *= max_force / len;
                    sep_steer_z *= max_force / len;
                }
            }
        }

        // Finalize alignment
        if (count_ali > 0) {
            ali_steer_x /= count_ali;
            ali_steer_y /= count_ali;
            ali_steer_z /= count_ali;
            float len = sqrtf(ali_steer_x*ali_steer_x + ali_steer_y*ali_steer_y + ali_steer_z*ali_steer_z);
            if (len > 1e-6f) {
                ali_steer_x /= len; ali_steer_y /= len; ali_steer_z /= len;
                ali_steer_x *= max_speed;
                ali_steer_y *= max_speed;
                ali_steer_z *= max_speed;
                ali_steer_x -= vx;
                ali_steer_y -= vy;
                ali_steer_z -= vz;
                len = sqrtf(ali_steer_x*ali_steer_x + ali_steer_y*ali_steer_y + ali_steer_z*ali_steer_z);
                if (len > max_force) {
                    ali_steer_x *= max_force / len;
                    ali_steer_y *= max_force / len;
                    ali_steer_z *= max_force / len;
                }
            }
        }

        // Finalize cohesion
        if (count_coh > 0) {
            coh_steer_x /= count_coh;
            coh_steer_y /= count_coh;
            coh_steer_z /= count_coh;
            float desired_x = coh_steer_x - px;
            float desired_y = coh_steer_y - py;
            float desired_z = coh_steer_z - pz;
            float desired_len = sqrtf(desired_x*desired_x + desired_y*desired_y + desired_z*desired_z);
            if (desired_len > 1e-6f) {
                desired_x /= desired_len; desired_y /= desired_len; desired_z /= desired_len;
                desired_x *= max_speed;
                desired_y *= max_speed;
                desired_z *= max_speed;
                coh_steer_x = desired_x - vx;
                coh_steer_y = desired_y - vy;
                coh_steer_z = desired_z - vz;
                float coh_len = sqrtf(coh_steer_x*coh_steer_x + coh_steer_y*coh_steer_y + coh_steer_z*coh_steer_z);
                if (coh_len > max_force) {
                    coh_steer_x *= max_force / coh_len;
                    coh_steer_y *= max_force / coh_len;
                    coh_steer_z *= max_force / coh_len;
                }
            }
        }

        out_sep[i*3]     = sep_steer_x;
        out_sep[i*3 + 1] = sep_steer_y;
        out_sep[i*3 + 2] = sep_steer_z;
        out_ali[i*3]     = ali_steer_x;
        out_ali[i*3 + 1] = ali_steer_y;
        out_ali[i*3 + 2] = ali_steer_z;
        out_coh[i*3]     = coh_steer_x;
        out_coh[i*3 + 1] = coh_steer_y;
        out_coh[i*3 + 2] = coh_steer_z;
    }
}