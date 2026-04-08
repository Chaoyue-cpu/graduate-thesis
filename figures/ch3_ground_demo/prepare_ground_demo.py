#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch
import numpy as np
import open3d as o3d

ZH_FONT = font_manager.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")

BASE_GRAY = np.array([0.80, 0.80, 0.80])
HIT_GREEN = np.array([0.16, 0.62, 0.28])

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def colorize(points: np.ndarray, mask: np.ndarray, hit_color, bg_color):
    colors = np.tile(np.asarray(bg_color, dtype=float), (len(points), 1))
    colors[mask] = np.asarray(hit_color, dtype=float)
    return colors


def add_panel(ax, pts, colors, title, mins, maxs, plane=None, plane_points=None):
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=colors, s=1.8, linewidths=0, alpha=0.95)
    if plane is not None:
        a, b, c, d = plane
        if plane_points is not None and len(plane_points) > 10:
            px = plane_points[:, 0]
            py = plane_points[:, 1]
            x0, x1 = np.percentile(px, [1, 99])
            y0, y1 = np.percentile(py, [1, 99])
            xpad = 0.08 * max(x1 - x0, 1e-3)
            ypad = 0.08 * max(y1 - y0, 1e-3)
            x0 -= xpad
            x1 += xpad
            y0 -= ypad
            y1 += ypad
        else:
            x0, x1 = mins[0], maxs[0]
            y0, y1 = mins[1], maxs[1]
        xx, yy = np.meshgrid(
            np.linspace(x0, x1, 26),
            np.linspace(y0, y1, 18),
        )
        if abs(c) > 1e-6:
            zz = -(a * xx + b * yy + d) / c
            inside = (zz >= mins[2] - 0.2) & (zz <= maxs[2] + 0.2)
            zz = np.where(inside, zz, np.nan)
            ax.plot_surface(xx, yy, zz, color="#3f79b7", alpha=0.62, linewidth=0, shade=False)

    if title:
        ax.set_title(title, fontsize=11.5, pad=10, fontproperties=ZH_FONT)
    ax.set_xlabel("X / m", labelpad=10)
    ax.set_ylabel("Y / m", labelpad=-1)
    ax.set_zlabel("")
    ax.view_init(elev=22, azim=-114)
    ax.grid(False)
    ax.set_xlim(mins[0], maxs[0])
    ax.set_ylim(mins[1], maxs[1])
    ax.set_zlim(mins[2], maxs[2])
    xr, yr, zr = maxs - mins
    ax.set_box_aspect((xr, yr, zr * 3.0))
    ax.tick_params(labelsize=7, pad=1, length=2.2, width=0.8)

    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis.pane.set_edgecolor((0.82, 0.82, 0.82, 1.0))
        axis.line.set_color((0.35, 0.35, 0.35, 1.0))

    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)
    ax.zaxis.label.set_size(9)
    ax.xaxis.set_rotate_label(False)
    ax.yaxis.set_rotate_label(False)

    # Sparse ticks are easier to read in the side-view layout.
    ax.set_xticks(np.linspace(int(np.floor(mins[0] / 10)) * 10, int(np.ceil(maxs[0] / 10)) * 10, 5))
    y_ticks = np.linspace(mins[1], maxs[1], 3)
    ax.set_yticks(np.round(y_ticks, 1))
    z_ticks = np.linspace(max(0.0, mins[2]), maxs[2], 5)
    ax.set_zticks(np.round(z_ticks, 1))

    # Put the z-axis label next to the left vertical ticks instead of the default right side.
    ax.text2D(
        -0.125,
        0.49,
        "Z / m",
        transform=ax.transAxes,
        rotation=90,
        va="center",
        ha="left",
        fontsize=9,
    )
def save_single_panel(output_path, pts, colors, title, mins, maxs, plane=None, plane_points=None):
    fig = plt.figure(figsize=(5.6, 4.9))
    ax = fig.add_subplot(111, projection="3d")
    add_panel(ax, pts, colors, title, mins, maxs, plane=plane, plane_points=plane_points)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.90)
    output_path = Path(output_path)
    fig.savefig(output_path, dpi=420, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(output_path.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def save_triptych(output_path, panels, mins, maxs):
    fig = plt.figure(figsize=(16.2, 6.2))
    axes = [
        fig.add_subplot(131, projection="3d"),
        fig.add_subplot(132, projection="3d"),
        fig.add_subplot(133, projection="3d"),
    ]
    fig.subplots_adjust(left=0.03, right=0.985, bottom=0.11, top=0.975, wspace=0.14)

    for ax, panel in zip(axes, panels):
        add_panel(
            ax,
            panel["pts"],
            panel["colors"],
            None,
            mins,
            maxs,
            plane=panel.get("plane"),
            plane_points=panel.get("plane_points"),
        )

    labels = ["原始点云", "候选地面点", "RANSAC 平面拟合"]
    for ax, label in zip(axes, labels):
        bbox = ax.get_position()
        xc = 0.5 * (bbox.x0 + bbox.x1)
        fig.text(
            xc,
            bbox.y0 + 0.075,
            label,
            ha="center",
            va="top",
            fontsize=12,
            fontproperties=ZH_FONT,
        )

    arrow_style = dict(arrowstyle="-|>", mutation_scale=9, lw=0.9, color="#777777")
    bbox1 = axes[0].get_position()
    bbox2 = axes[1].get_position()
    bbox3 = axes[2].get_position()
    y_arrow = 0.5 * (bbox1.y0 + bbox1.y1)
    arrow_half = 0.010
    gap_shift = -0.018
    gap12_center = 0.5 * (bbox1.x1 + bbox2.x0) + gap_shift
    gap23_center = 0.5 * (bbox2.x1 + bbox3.x0) + gap_shift
    fig.add_artist(
        FancyArrowPatch(
            (gap12_center - arrow_half, y_arrow),
            (gap12_center + arrow_half, y_arrow),
            transform=fig.transFigure,
            **arrow_style,
        )
    )
    fig.add_artist(
        FancyArrowPatch(
            (gap23_center - arrow_half, y_arrow),
            (gap23_center + arrow_half, y_arrow),
            transform=fig.transFigure,
            **arrow_style,
        )
    )

    output_path = Path(output_path)
    fig.savefig(output_path, dpi=420, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(output_path.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="/home/scy/catkin_ws_hdl_location/地面展示/1722674951.282918.pcd",
        help="Input PCD file",
    )
    parser.add_argument(
        "--output-dir",
        default="figures/ch3_ground_demo",
        help="Directory for generated previews and point clouds",
    )
    parser.add_argument("--tilt-deg", type=float, default=0.0, help="Pitch compensation angle in degrees.")
    parser.add_argument(
        "--height-clip-range",
        type=float,
        default=0.60,
        help="Height band half-width for candidate ground extraction.",
    )
    parser.add_argument(
        "--normal-filter-thresh-deg",
        type=float,
        default=20.0,
        help="Keep points whose normals are within this angle to the vertical direction.",
    )
    parser.add_argument(
        "--floor-normal-thresh-deg",
        type=float,
        default=10.0,
        help="Reject fitted planes whose normals deviate too much from the vertical direction.",
    )
    parser.add_argument(
        "--ransac-dist",
        type=float,
        default=0.05,
        help="RANSAC distance threshold.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), output_dir / Path(__file__).name)

    pcd = o3d.io.read_point_cloud(str(input_path))
    pts = np.asarray(pcd.points)
    if pts.size == 0:
        raise RuntimeError(f"Empty point cloud: {input_path}")

    # Remove far outliers to make the figure clearer.
    x_min, x_max = np.percentile(pts[:, 0], [1, 99])
    y_min, y_max = np.percentile(pts[:, 1], [1, 99])
    z_min, z_max = np.percentile(pts[:, 2], [1, 99])
    crop_mask = (
        (pts[:, 0] >= x_min)
        & (pts[:, 0] <= x_max)
        & (pts[:, 1] >= y_min)
        & (pts[:, 1] <= y_max)
        & (pts[:, 2] >= z_min - 0.3)
        & (pts[:, 2] <= z_max + 0.3)
    )
    crop_idx = np.where(crop_mask)[0]
    pcd = pcd.select_by_index(crop_idx)
    pts = np.asarray(pcd.points)

    # The processing order follows the logic in floor_detection_nodelet.cpp:
    # tilt compensation -> height clipping -> normal filtering -> RANSAC plane fitting.
    if abs(args.tilt_deg) > 1e-6:
        tilt = o3d.geometry.get_rotation_matrix_from_axis_angle(
            np.array([0.0, np.deg2rad(args.tilt_deg), 0.0])
        )
        pts = (tilt @ pts.T).T
        pcd.points = o3d.utility.Vector3dVector(pts)

    z_floor_seed = float(np.percentile(pts[:, 2], 10))
    z_low = z_floor_seed - 0.15
    z_high = z_floor_seed + args.height_clip_range
    candidate_mask = (pts[:, 2] >= z_low) & (pts[:, 2] <= z_high)
    candidate_idx = np.where(candidate_mask)[0]
    candidate_pcd = pcd.select_by_index(candidate_idx)

    candidate_pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamKNN(knn=10)
    )
    candidate_pcd.orient_normals_towards_camera_location(
        np.array([0.0, 0.0, float(np.max(pts[:, 2]) + 2.0)])
    )
    cand_normals = np.asarray(candidate_pcd.normals)
    vertical = np.array([0.0, 0.0, 1.0])
    keep_normal = np.abs(cand_normals @ vertical) >= np.cos(
        np.deg2rad(args.normal_filter_thresh_deg)
    )
    candidate_idx = candidate_idx[np.where(keep_normal)[0]]
    candidate_mask = np.zeros(len(pts), dtype=bool)
    candidate_mask[candidate_idx] = True
    candidate_pcd = pcd.select_by_index(candidate_idx)

    plane_model, inlier_idx_local = candidate_pcd.segment_plane(
        distance_threshold=args.ransac_dist, ransac_n=3, num_iterations=1000
    )
    plane_normal = np.asarray(plane_model[:3], dtype=float)
    plane_normal /= np.linalg.norm(plane_normal)
    if np.dot(plane_normal, vertical) < 0:
        plane_model = [-plane_model[0], -plane_model[1], -plane_model[2], -plane_model[3]]
        plane_normal *= -1.0
    if abs(np.dot(plane_normal, vertical)) < np.cos(np.deg2rad(args.floor_normal_thresh_deg)):
        raise RuntimeError("Detected plane is not vertical enough to be considered floor.")
    inlier_idx_local = np.asarray(inlier_idx_local, dtype=int)
    inlier_idx = candidate_idx[inlier_idx_local]
    inlier_mask = np.zeros(len(pts), dtype=bool)
    inlier_mask[inlier_idx] = True

    # Save colored point clouds for manual screenshot.
    raw_pcd = o3d.geometry.PointCloud()
    raw_pcd.points = o3d.utility.Vector3dVector(pts)
    raw_pcd.colors = o3d.utility.Vector3dVector(
        np.tile(BASE_GRAY, (len(pts), 1))
    )

    cand_pcd = o3d.geometry.PointCloud()
    cand_pcd.points = o3d.utility.Vector3dVector(pts)
    cand_pcd.colors = o3d.utility.Vector3dVector(
        colorize(pts, candidate_mask, HIT_GREEN, BASE_GRAY)
    )

    fit_pcd = o3d.geometry.PointCloud()
    fit_pcd.points = o3d.utility.Vector3dVector(pts)
    fit_pcd.colors = o3d.utility.Vector3dVector(
        colorize(pts, inlier_mask, HIT_GREEN, BASE_GRAY)
    )

    o3d.io.write_point_cloud(str(output_dir / "01_raw_scene.ply"), raw_pcd)
    o3d.io.write_point_cloud(str(output_dir / "02_ground_candidates.ply"), cand_pcd)
    o3d.io.write_point_cloud(str(output_dir / "03_ground_plane_inliers.ply"), fit_pcd)

    mins = np.array(
        [
            np.percentile(pts[:, 0], 2),
            np.percentile(pts[:, 1], 2),
            np.percentile(pts[:, 2], 5),
        ]
    )
    maxs = np.array(
        [
            np.percentile(pts[:, 0], 98),
            np.percentile(pts[:, 1], 98),
            np.percentile(pts[:, 2], 97),
        ]
    )
    mins[2] -= 0.15
    maxs[2] += 0.15

    save_single_panel(
        output_dir / "01_raw_scene.png",
        pts,
        np.tile(BASE_GRAY[None, :], (len(pts), 1)),
        "原始点云",
        mins,
        maxs,
    )
    save_single_panel(
        output_dir / "02_ground_candidates.png",
        pts,
        colorize(pts, candidate_mask, HIT_GREEN, BASE_GRAY),
        "候选地面点",
        mins,
        maxs,
    )
    save_single_panel(
        output_dir / "03_ground_plane_inliers.png",
        pts,
        colorize(pts, inlier_mask, HIT_GREEN, BASE_GRAY),
        "RANSAC 平面拟合",
        mins,
        maxs,
        plane=plane_model,
        plane_points=pts[inlier_mask],
    )
    save_triptych(
        output_dir / "00_ground_extraction_pipeline.png",
        [
            {
                "pts": pts,
                "colors": np.tile(BASE_GRAY[None, :], (len(pts), 1)),
            },
            {
                "pts": pts,
                "colors": colorize(pts, candidate_mask, HIT_GREEN, BASE_GRAY),
            },
            {
                "pts": pts,
                "colors": colorize(pts, inlier_mask, HIT_GREEN, BASE_GRAY),
                "plane": plane_model,
                "plane_points": pts[inlier_mask],
            },
        ],
        mins,
        maxs,
    )

    (output_dir / "README.txt").write_text(
        "\n".join(
            [
                "图 3.6 地面点提取与平面拟合效果图素材",
                "处理流程参考 /home/scy/catkin_ws_hdl_location/src/hdl_localization-master/scripts/floor_detection_nodelet.cpp",
                "",
                "文件说明：",
                "01_raw_scene.ply               原始点云",
                "02_ground_candidates.ply       候选地面点高亮结果",
                "03_ground_plane_inliers.ply    RANSAC 地面内点高亮结果",
                "01_raw_scene.png               原始点云独立图片",
                "01_raw_scene.pdf               原始点云矢量版图片",
                "02_ground_candidates.png       候选地面点独立图片",
                "02_ground_candidates.pdf       候选地面点矢量版图片",
                "03_ground_plane_inliers.png    RANSAC 平面拟合独立图片",
                "03_ground_plane_inliers.pdf    RANSAC 平面拟合矢量版图片",
                "00_ground_extraction_pipeline.png  三联流程图图片",
                "00_ground_extraction_pipeline.pdf  三联流程图矢量版图片",
                "",
                "若需要手动截图：",
                "1. 用 Open3D / CloudCompare 打开上述 ply 文件。",
                "2. 建议白底、透视视图，保持三个视角一致。",
                "3. 截图顺序依次为原始点云、候选地面点、RANSAC 平面拟合。",
                "4. 颜色建议保持灰色点云、绿色地面点、蓝色拟合平面。",
                "",
                "若需要手动调图，优先调整以下参数：",
                "1. view_init(elev, azim)：控制三维视角。",
                "2. scatter 的 s 和 alpha：控制点大小与透明度。",
                "3. z_low / z_high：控制候选地面点高度范围。",
                "4. normal_filter_thresh_deg：控制法向筛选强度。",
                "5. ransac_dist：控制平面拟合内点距离阈值。",
                "6. mins / maxs：控制坐标轴显示范围。",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Generated files in: {output_dir}")
    print(f"plane_model: {plane_model}")
    print(f"z_floor_seed: {z_floor_seed:.4f}, clip=[{z_low:.4f}, {z_high:.4f}]")
    print(f"candidate_points: {candidate_mask.sum()} / {len(pts)}")
    print(f"ground_inliers: {inlier_mask.sum()} / {len(pts)}")


if __name__ == "__main__":
    main()
