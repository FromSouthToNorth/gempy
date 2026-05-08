"""
02 — 背斜(Anticline)构造

在 [0, 2000] x [0, 2000] 范围内构造一个东西向的背斜:
- 顶面方程 z_top = 800 - k*(x-1000)^2
- 底面方程 z_bot = 500 - k*(x-1000)^2
- 西翼下倾向西、东翼下倾向东、轴部水平

关键点:产状(pole_vector)是层面法向量,对沉积"向上"的层指向上方。
- 西翼:层向东上升 → 法向量 = (-sinθ, 0, cosθ)
- 轴部:水平 → (0, 0, 1)
- 东翼:层向东下降 → 法向量 = (+sinθ, 0, cosθ)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gempy as gp
import gempy_viewer as gpv
import matplotlib.pyplot as plt
import numpy as np

from gempy_demo import save_2d_figure


CURVATURE = 3e-4   # k:控制褶皱锐度
CREST_X = 1000     # 轴部 x 位置
TOP_Z = 800        # 轴部顶面深度
BOT_Z = 500        # 轴部底面深度


def fold_z(x: np.ndarray, base: float) -> np.ndarray:
    return base - CURVATURE * (x - CREST_X) ** 2


def _build_structural_frame() -> gp.data.StructuralFrame:
    """创建包含 top、bottom 两个 element 的结构框架。"""
    frame = gp.data.StructuralFrame.initialize_default_structure()
    frame.structural_groups[0].elements[0].name = "top"
    frame.structural_groups[0].elements[0].color = "#FF5733"

    empty_sp = np.array([], dtype=gp.data.SurfacePointsTable.dt)
    empty_or = np.array([], dtype=gp.data.OrientationsTable.dt)
    el = gp.data.StructuralElement(
        name="bottom",
        color="#33FF57",
        surface_points=gp.data.SurfacePointsTable(data=empty_sp),
        orientations=gp.data.OrientationsTable(data=empty_or),
    )
    frame.structural_groups[0].append_element(el)
    return frame


def build_model() -> gp.data.GeoModel:
    geo_model = gp.create_geomodel(
        project_name="anticline",
        extent=[0, 2000, 0, 2000, 0, 1000],
        resolution=[60, 30, 60],
        refinement=4,
        structural_frame=_build_structural_frame(),
    )

    xs = np.linspace(150, 1850, 9)
    z_top = fold_z(xs, TOP_Z)
    z_bot = fold_z(xs, BOT_Z)

    gp.add_surface_points(
        geo_model=geo_model,
        x=np.concatenate([xs, xs]).tolist(),
        y=[1000.0] * (len(xs) * 2),
        z=np.concatenate([z_top, z_bot]).tolist(),
        elements_names=["top"] * len(xs) + ["bottom"] * len(xs),
    )

    dip_deg = 25.0
    s, c = math.sin(math.radians(dip_deg)), math.cos(math.radians(dip_deg))
    gp.add_orientations(
        geo_model=geo_model,
        x=[300.0, CREST_X, 1700.0],
        y=[1000.0, 1000.0, 1000.0],
        z=[fold_z(np.array([300.0]), TOP_Z)[0],
           TOP_Z,
           fold_z(np.array([1700.0]), TOP_Z)[0]],
        elements_names=["top", "top", "top"],
        pole_vector=[
            [-s, 0.0, c],   # 西翼
            [0.0, 0.0, 1.0],
            [+s, 0.0, c],   # 东翼
        ],
    )

    gp.compute_model(geo_model)
    return geo_model


def main() -> None:
    geo_model = build_model()
    print(geo_model.structural_frame)

    gpv.plot_2d(geo_model, direction=["y"], show_data=True)
    out = save_2d_figure("02_anticline")
    print(f"已保存 2D 截面: {out}")
    plt.close("all")

    gpv.plot_3d(geo_model, show_data=True, show_lith=True, image=False)


if __name__ == "__main__":
    main()
