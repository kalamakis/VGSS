import numpy as np

from bgs.sampling import VGSSSamplingStats, sample_on_vgss

# ==========================================
# 1. GEOMETRY & CONDUCTOR PARSER
# ==========================================

def get_system_bounds(conductors):
    all_mins = np.array([c.min_bounds for c in conductors])
    all_maxs = np.array([c.max_bounds for c in conductors])
    g_min = np.min(all_mins, axis=0)
    g_max = np.max(all_maxs, axis=0)
    system_center = (g_max + g_min) / 2.0
    system_size = np.max(g_max - g_min)
    return system_center, system_size

# ==========================================
# 2. PURE RANDOM WALK LOGIC
# ==========================================

def sample_point_on_bgs(bgs_min, bgs_max, rng):
    dx, dy, dz = bgs_max - bgs_min
    areas = [dy*dz, dy*dz, dx*dz, dx*dz, dx*dy, dx*dy]
    total_area = sum(areas)

    face_probs = [a / total_area for a in areas]
    face_idx = rng.choice(6, p=face_probs)

    p = np.zeros(3)
    u, v = rng.random(2)

    if face_idx == 0:   p = [bgs_min[0], bgs_min[1] + u*dy, bgs_min[2] + v*dz]
    elif face_idx == 1: p = [bgs_max[0], bgs_min[1] + u*dy, bgs_min[2] + v*dz]
    elif face_idx == 2: p = [bgs_min[0] + u*dx, bgs_min[1], bgs_min[2] + v*dz]
    elif face_idx == 3: p = [bgs_min[0] + u*dx, bgs_max[1], bgs_min[2] + v*dz]
    elif face_idx == 4: p = [bgs_min[0] + u*dx, bgs_min[1] + v*dy, bgs_min[2]]
    else:               p = [bgs_min[0] + u*dx, bgs_min[1] + v*dy, bgs_max[2]]

    return np.array(p)


def sample_point_on_maximal_cube(p_center, radius, rng):
    cube_min = p_center - radius
    cube_max = p_center + radius
    return sample_point_on_bgs(cube_min, cube_max, rng)


def run_frw_geometry(conductors, master_vgss, rng, num_walks=1000, max_hops=100):
    sys_center, sys_size = get_system_bounds(conductors)
    math_kill_radius = sys_size * 1000.0

    all_walk_data = []
    sampling_stats = VGSSSamplingStats()


    for walk in range(num_walks):
        percent_done = (walk + 1) / num_walks * 100.0
        print(f"\rProgress: {percent_done:.1f}% ({walk + 1}/{num_walks})", end="", flush=True)

        current_p = sample_on_vgss(
            master_vgss.sampling_context,
            rng,
            stats=sampling_stats,
        )
        start_point = current_p.copy()
        current_walk_path = []
        hit_target = None

        for hop in range(max_hops):
            dist_to_center = np.max(np.abs(current_p - sys_center))
            if dist_to_center > math_kill_radius:
                hit_target = "Infinity (Ground)"
                break

            distances = [c.distance_to_point(current_p) for c in conductors]
            min_dist = min(distances)

            nearest_idx = np.argmin(distances)
            side_a = 2 * min_dist

            # SAVING BOTH CENTER AND SIDE LENGTH
            current_walk_path.append({
                "center": current_p.tolist(),
                "a": float(side_a)
            })

            if min_dist < 1e-4:
                hit_target = conductors[nearest_idx].name
                break

            current_p = sample_point_on_maximal_cube(current_p, min_dist, rng)

        all_walk_data.append({
            "start_point": start_point.tolist(),
            "path_data": current_walk_path,
            "hit_conductor": hit_target
        })

    return {
        "H": sampling_stats.estimate_H(master_vgss.sampling_context),
        "sampling_stats": sampling_stats.as_dict(master_vgss.sampling_context),
        "walks": all_walk_data
    }


# ==========================================
# 5. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print(
        "Run FRW via CLI module: python -m FRW.cli <input_file.m>"
    )
