import numpy as np
import sys
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import CheckButtons

from bgs.matlab_parser import parse_matlab_geometry
from bgs.sampling import VGSSSamplingStats, sample_on_vgss
from bgs.vgss import build_all_net_vgss

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
# 3. 2D VISUALIZATION
# ==========================================

def visualize_2d_walk(conductors, master_vgss, rng):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    master_names = set(master_vgss.net.conductor_names)
    
    sys_center, sys_size = get_system_bounds(conductors)
    visual_kill_radius = sys_size * 2.0 
    
    path_points = []
    maximal_squares = [] 
    
    current_p = sample_on_vgss(master_vgss.sampling_context, rng)
    path_points.append(current_p.copy())
    
    print(f"\n[2D VISUALIZATION WALK LOG]")
    
    max_hops = 100
    for hop in range(max_hops):
        if np.max(np.abs(current_p - sys_center)) > visual_kill_radius:
            print(f"TERMINATED: Escaped to Infinity (Ground)")
            break
            
        distances = [c.distance_to_point(current_p) for c in conductors]
        min_dist = min(distances)
        maximal_squares.append((current_p.copy(), min_dist))
        
        print(f"Hop {hop + 1}: Center = [{current_p[0]:.4f}, {current_p[1]:.4f}, {current_p[2]:.4f}], a = {2*min_dist:.4f}")
        
        if min_dist < 1e-4:
            hit_name = conductors[np.argmin(distances)].name
            print(f"TERMINATED ON: {hit_name}")
            break
            
        current_p = sample_point_on_maximal_cube(current_p, min_dist, rng)
        path_points.append(current_p.copy())
        
    path_points = np.array(path_points)

    # Λίστα για να κρατάμε αναφορές σε όλα τα maximal squares των 3 επιπέδων
    square_patches = []

    # --- XY PROJECTION ---
    ax1.set_title("Top View (XY Plane)", fontsize=12, fontweight='bold')
    for i, c in enumerate(conductors):
        color = 'red' if c.name in master_names else 'darkgray'
        dx = c.max_bounds[0] - c.min_bounds[0]
        dy = c.max_bounds[1] - c.min_bounds[1]
        rect = patches.Rectangle((c.min_bounds[0], c.min_bounds[1]), dx, dy, edgecolor='black', facecolor=color, alpha=0.5, label=c.name)
        ax1.add_patch(rect)
    for surface in master_vgss.surfaces:
        bgs_min, bgs_max = surface.min_bounds, surface.max_bounds
        bgs_dx = bgs_max[0] - bgs_min[0]
        bgs_dy = bgs_max[1] - bgs_min[1]
        ax1.add_patch(patches.Rectangle((bgs_min[0], bgs_min[1]), bgs_dx, bgs_dy, edgecolor='black', linestyle='--', facecolor='none', linewidth=1.5, label='BGS'))
    
    for center, r in maximal_squares:
        p1 = patches.Rectangle((center[0] - r, center[1] - r), 2*r, 2*r, facecolor='purple', edgecolor='none', alpha=0.15, zorder=3)
        p2 = patches.Rectangle((center[0] - r, center[1] - r), 2*r, 2*r, facecolor='none', edgecolor='purple', linewidth=1.5, zorder=4)
        ax1.add_patch(p1)
        ax1.add_patch(p2)
        square_patches.extend([p1, p2])

    if len(path_points) > 0:
        ax1.plot(path_points[:, 0], path_points[:, 1], color='black', marker='o', markersize=5, linewidth=1.5, zorder=5, label="Walk Path")
        ax1.scatter(path_points[-1, 0], path_points[-1, 1], color='crimson', s=100, marker='X', zorder=6)
    ax1.set_xlabel('X Coordinate')
    ax1.set_ylabel('Y Coordinate')
    ax1.grid(True, linestyle=':', alpha=0.5)

    # --- XZ PROJECTION ---
    ax2.set_title("Front View (XZ Plane)", fontsize=12, fontweight='bold')
    for i, c in enumerate(conductors):
        color = 'red' if c.name in master_names else 'darkgray'
        dx = c.max_bounds[0] - c.min_bounds[0]
        dz = c.max_bounds[2] - c.min_bounds[2]
        ax2.add_patch(patches.Rectangle((c.min_bounds[0], c.min_bounds[2]), dx, dz, edgecolor='black', facecolor=color, alpha=0.5))
    for surface in master_vgss.surfaces:
        bgs_min, bgs_max = surface.min_bounds, surface.max_bounds
        bgs_dx = bgs_max[0] - bgs_min[0]
        bgs_dz = bgs_max[2] - bgs_min[2]
        ax2.add_patch(patches.Rectangle((bgs_min[0], bgs_min[2]), bgs_dx, bgs_dz, edgecolor='black', linestyle='--', facecolor='none', linewidth=1.5))
    
    for center, r in maximal_squares:
        p1 = patches.Rectangle((center[0] - r, center[2] - r), 2*r, 2*r, facecolor='purple', edgecolor='none', alpha=0.15, zorder=3)
        p2 = patches.Rectangle((center[0] - r, center[2] - r), 2*r, 2*r, facecolor='none', edgecolor='purple', linewidth=1.5, zorder=4)
        ax2.add_patch(p1)
        ax2.add_patch(p2)
        square_patches.extend([p1, p2])

    if len(path_points) > 0:
        ax2.plot(path_points[:, 0], path_points[:, 2], color='black', marker='o', markersize=5, linewidth=1.5, zorder=5)
        ax2.scatter(path_points[-1, 0], path_points[-1, 2], color='crimson', s=100, marker='X', zorder=6)
    ax2.set_xlabel('X Coordinate')
    ax2.set_ylabel('Z Coordinate')
    ax2.grid(True, linestyle=':', alpha=0.5)

    # --- YZ PROJECTION ---
    ax3.set_title("Side View (YZ Plane)", fontsize=12, fontweight='bold')
    for i, c in enumerate(conductors):
        color = 'red' if c.name in master_names else 'darkgray'
        dy = c.max_bounds[1] - c.min_bounds[1]
        dz = c.max_bounds[2] - c.min_bounds[2]
        ax3.add_patch(patches.Rectangle((c.min_bounds[1], c.min_bounds[2]), dy, dz, edgecolor='black', facecolor=color, alpha=0.5))
    for surface in master_vgss.surfaces:
        bgs_min, bgs_max = surface.min_bounds, surface.max_bounds
        bgs_dy = bgs_max[1] - bgs_min[1]
        bgs_dz = bgs_max[2] - bgs_min[2]
        ax3.add_patch(patches.Rectangle((bgs_min[1], bgs_min[2]), bgs_dy, bgs_dz, edgecolor='black', linestyle='--', facecolor='none', linewidth=1.5))
    
    for center, r in maximal_squares:
        p1 = patches.Rectangle((center[1] - r, center[2] - r), 2*r, 2*r, facecolor='purple', edgecolor='none', alpha=0.15, zorder=3)
        p2 = patches.Rectangle((center[1] - r, center[2] - r), 2*r, 2*r, facecolor='none', edgecolor='purple', linewidth=1.5, zorder=4)
        ax3.add_patch(p1)
        ax3.add_patch(p2)
        square_patches.extend([p1, p2])

    if len(path_points) > 0:
        ax3.plot(path_points[:, 1], path_points[:, 2], color='black', marker='o', markersize=5, linewidth=1.5, zorder=5)
        ax3.scatter(path_points[-1, 1], path_points[-1, 2], color='crimson', s=100, marker='X', zorder=6)
    ax3.set_xlabel('Y Coordinate')
    ax3.set_ylabel('Z Coordinate')
    ax3.grid(True, linestyle=':', alpha=0.5)

    all_mins = np.array([c.min_bounds for c in conductors])
    all_maxs = np.array([c.max_bounds for c in conductors])
    g_min = np.min(all_mins, axis=0)
    g_max = np.max(all_maxs, axis=0)
    margin = (g_max - g_min) * 0.2
    
    ax1.set_xlim(g_min[0] - margin[0], g_max[0] + margin[0])
    ax1.set_ylim(g_min[1] - margin[1], g_max[1] + margin[1])
    ax1.set_aspect('equal')
    ax2.set_xlim(g_min[0] - margin[0], g_max[0] + margin[0])
    ax2.set_ylim(g_min[2] - margin[2], g_max[2] + margin[2])
    ax2.set_aspect('equal')
    ax3.set_xlim(g_min[1] - margin[1], g_max[1] + margin[1])
    ax3.set_ylim(g_min[2] - margin[2], g_max[2] + margin[2])
    ax3.set_aspect('equal')
    
    handles, labels = ax1.get_legend_handles_labels()
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    ax1.legend(*zip(*unique), loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3)

    # --- ΔΙΑΔΡΑΣΤΙΚΟ ΚΟΥΜΠΙ (CHECKBOX) ---
    plt.subplots_adjust(bottom=0.2) # Αφήνουμε χώρο στο κάτω μέρος
    rax = plt.axes([0.45, 0.02, 0.15, 0.05]) # Θέση του checkbox [left, bottom, width, height]
    check = CheckButtons(rax, ['Maximal Squares'], [True])
    
    def toggle_squares(label):
        status = check.get_status()[0]
        for patch in square_patches:
            patch.set_visible(status)
        plt.draw()
        
    check.on_clicked(toggle_squares)
    fig.custom_check_attr = check # Σημαντικό: Κρατάει το widget ζωντανό στη μνήμη

    plt.show()

# ==========================================
# 4. 3D VISUALIZATION
# ==========================================

def draw_cuboid(ax, min_bounds, max_bounds, color, alpha=0.5, wireframe=False):
    x = [min_bounds[0], max_bounds[0]]
    y = [min_bounds[1], max_bounds[1]]
    z = [min_bounds[2], max_bounds[2]]
    
    vertices = np.array([
        [x[0], y[0], z[0]], [x[1], y[0], z[0]], [x[1], y[1], z[0]], [x[0], y[1], z[0]],
        [x[0], y[0], z[1]], [x[1], y[0], z[1]], [x[1], y[1], z[1]], [x[0], y[1], z[1]]
    ])
    
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]], 
        [vertices[4], vertices[5], vertices[6], vertices[7]], 
        [vertices[0], vertices[1], vertices[5], vertices[4]], 
        [vertices[2], vertices[3], vertices[7], vertices[6]], 
        [vertices[1], vertices[2], vertices[6], vertices[5]], 
        [vertices[0], vertices[3], vertices[7], vertices[4]]  
    ]
    
    if wireframe:
        collection = Poly3DCollection(faces, linewidths=1.5, edgecolors=color, alpha=0.0)
    else:
        collection = Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors='black', alpha=alpha)
    ax.add_collection3d(collection)
    return collection


def visualize_3d_walk(conductors, master_vgss, rng):
    fig = plt.figure(figsize=(10, 10)) 
    ax = fig.add_subplot(111, projection='3d')
    master_names = set(master_vgss.net.conductor_names)
    
    sys_center, sys_size = get_system_bounds(conductors)
    visual_kill_radius = sys_size * 2.0 
    
    path_points = []
    maximal_squares = []
    
    current_p = sample_on_vgss(master_vgss.sampling_context, rng)
    path_points.append(current_p.copy())
    
    print(f"\n[3D VISUALIZATION WALK LOG]")
    
    max_hops = 100
    for hop in range(max_hops):
        if np.max(np.abs(current_p - sys_center)) > visual_kill_radius:
            print(f"TERMINATED: Escaped to Infinity (Ground)")
            break
            
        distances = [c.distance_to_point(current_p) for c in conductors]
        min_dist = min(distances)
        maximal_squares.append((current_p.copy(), min_dist))
        
        print(f"Hop {hop + 1}: Center = [{current_p[0]:.4f}, {current_p[1]:.4f}, {current_p[2]:.4f}], a = {2*min_dist:.4f}")
        
        if min_dist < 1e-4:
            hit_name = conductors[np.argmin(distances)].name
            print(f"TERMINATED ON: {hit_name}")
            break
            
        current_p = sample_point_on_maximal_cube(current_p, min_dist, rng)
        path_points.append(current_p.copy())
        
    path_points = np.array(path_points)

    for i, c in enumerate(conductors):
        color = 'red' if c.name in master_names else 'darkgray'
        draw_cuboid(ax, c.min_bounds, c.max_bounds, color=color, alpha=0.2) 
        
    for surface in master_vgss.surfaces:
        draw_cuboid(ax, surface.min_bounds, surface.max_bounds, color='black', wireframe=True)
    
    # Λίστα για τα 3D collections των κύβων
    cube_collections = []
    for center, r in maximal_squares:
        cube_min = center - r
        cube_max = center + r
        coll = draw_cuboid(ax, cube_min, cube_max, color='purple', wireframe=True)
        cube_collections.append(coll)

    if len(path_points) > 0:
        ax.plot(path_points[:, 0], path_points[:, 1], path_points[:, 2], color='black', marker='o', markersize=5, linewidth=2, label='Walk Path')
        ax.scatter(path_points[-1, 0], path_points[-1, 1], path_points[-1, 2], color='crimson', s=100, marker='X', label='Hit Terminal')

    all_mins = np.array([c.min_bounds for c in conductors])
    all_maxs = np.array([c.max_bounds for c in conductors])
    g_min = np.min(all_mins, axis=0)
    g_max = np.max(all_maxs, axis=0)
    
    max_range = np.array([
        g_max[0] - g_min[0], 
        g_max[1] - g_min[1], 
        g_max[2] - g_min[2]
    ]).max()
    
    mid_x = (g_max[0] + g_min[0]) * 0.5
    mid_y = (g_max[1] + g_min[1]) * 0.5
    mid_z = (g_max[2] + g_min[2]) * 0.5
    
    ax.set_xlim(mid_x - max_range * 0.5, mid_x + max_range * 0.5)
    ax.set_ylim(mid_y - max_range * 0.5, mid_y + max_range * 0.5)
    ax.set_zlim(mid_z - max_range * 0.5, mid_z + max_range * 0.5)
    
    try:
        ax.set_box_aspect((1, 1, 1)) 
    except AttributeError:
        pass 
        
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Floating Random Walk (Perfect Aspect Ratio)')

    # --- ΔΙΑΔΡΑΣΤΙΚΟ ΚΟΥΜΠΙ (CHECKBOX) ΓΙΑ 3D ---
    rax = plt.axes([0.02, 0.02, 0.15, 0.05]) # Θέση κάτω αριστερά
    check = CheckButtons(rax, ['Maximal Cubes'], [True])
    
    def toggle_cubes(label):
        status = check.get_status()[0]
        for coll in cube_collections:
            coll.set_visible(status)
        plt.draw()
        
    check.on_clicked(toggle_cubes)
    fig.custom_check_attr = check # Κρατάει το widget ζωντανό

    plt.show()


# ==========================================
# 5. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Error: No input file provided.")
        print("Usage: python -m FRW.random_walk <input_file.m>")
        sys.exit(1)

    filename = sys.argv[1]
    print(f"Reading geometry from {filename}...\n")

    try:
        system_conductors = parse_matlab_geometry(filename)
    except FileNotFoundError:
        print(f"ERROR: Could not find '{filename}'")
        sys.exit(1)

    if not system_conductors:
        print("No conductors found in the file.")
        sys.exit(1)

    print("Parsed Conductors:")
    for c in system_conductors:
        print(c)

    all_net_vgss = build_all_net_vgss(
        system_conductors,
        scale_factor=1.25,
        max_distance=10.0,
    )
    master_vgss = all_net_vgss[0]
    rng = np.random.default_rng(1234)

    # Visualizations print their path data before rendering.
    # visualize_2d_walk(system_conductors, master_vgss, rng)
    visualize_3d_walk(system_conductors, master_vgss, rng)

    print("\nExecuting Batch Geometric Walk Engine...")
    print(f"Master Net: {master_vgss.net.name}")
    print(f"Conductors: {', '.join(master_vgss.net.conductor_names)}")
    print("-" * 30)

    n_walks = 5000
    export_data = run_frw_geometry(
        system_conductors,
        master_vgss,
        rng,
        num_walks=n_walks,
    )

    print(f"Total Walks Completed: {len(export_data['walks'])}")
    print(f"Estimated H: {export_data['H']:.6f}")

    output_filename = "output/frw_exported_data.json"
    print(f"\nExporting all walk data to {output_filename}...")

    with open(output_filename, "w") as outfile:
        json.dump(export_data, outfile, indent=4)

    print(f"Success! Data for {n_walks} walks successfully saved.")
