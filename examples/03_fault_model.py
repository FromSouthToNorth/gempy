"""
03 — 含正断层(Normal Fault)的双层模型

场景:东西走向、近垂直的正断层切过两套水平地层。
- 模型范围: 2000 x 1000 x 1000
- 断层面在 x ≈ 1000,近垂直
- 西盘(上盘)地层位于较高位置,东盘(下盘)位移下降 200 m

GemPy v2025 断层处理流程:
1. 创建两个 StructuralGroup:Fault_Series(断层,FAULT 关系)在前,
   Strat_Series(地层,ERODE 关系)在后。
2. 断层组在前意味着它"切"位于其后的地层组。
3. 用 `gp.set_is_fault` 标记断层关系。

注:element 必须在 structural_frame 中预先创建。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gempy as gp
import gempy_viewer as gpv
import matplotlib.pyplot as plt
import numpy as np

from gempy_demo import save_2d_figure


def _build_structural_frame() -> gp.data.StructuralFrame:
    """创建两组:Fault_Series(断层) + Strat_Series(地层),断层在前。"""
    empty_sp = np.array([], dtype=gp.data.SurfacePointsTable.dt)
    empty_or = np.array([], dtype=gp.data.OrientationsTable.dt)

    # --- 断层组(在前,后切地层) ---
    fault_el = gp.data.StructuralElement(
        name="fault",
        color="#AA0000",
        surface_points=gp.data.SurfacePointsTable(data=empty_sp),
        orientations=gp.data.OrientationsTable(data=empty_or),
    )
    fault_group = gp.data.StructuralGroup(
        name="Fault_Series",
        elements=[fault_el],
        structural_relation=gp.data.StackRelationType.FAULT,
    )

    # --- 地层组(在后,被断层切割) ---
    top_el = gp.data.StructuralElement(
        name="top",
        color="#FF5733",
        surface_points=gp.data.SurfacePointsTable(data=empty_sp),
        orientations=gp.data.OrientationsTable(data=empty_or),
    )
    bot_el = gp.data.StructuralElement(
        name="bottom",
        color="#33FF57",
        surface_points=gp.data.SurfacePointsTable(data=empty_sp),
        orientations=gp.data.OrientationsTable(data=empty_or),
    )
    strat_group = gp.data.StructuralGroup(
        name="Strat_Series",
        elements=[top_el, bot_el],
        structural_relation=gp.data.StackRelationType.ERODE,
    )

    frame = gp.data.StructuralFrame(
        structural_groups=[fault_group, strat_group],
        color_gen=gp.core.color_generator.ColorsGenerator(),
    )
    return frame


def build_model() -> gp.data.GeoModel:
    geo_model = gp.create_geomodel(
        project_name="fault_model",
        extent=[0, 2000, 0, 1000, 0, 1000],
        resolution=[60, 30, 60],
        refinement=4,
        structural_frame=_build_structural_frame(),
    )

    # ---- 1) 地层接触面(西高东低,断层错动 ~200m) ----
    gp.add_surface_points(
        geo_model=geo_model,
        x=[200, 600,   1400, 1800,   200, 600,   1400, 1800],
        y=[500] * 8,
        z=[700, 700,   500, 500,    400, 400,   200, 200],
        elements_names=[
            "top", "top", "top", "top",
            "bottom", "bottom", "bottom", "bottom",
        ],
    )

    # ---- 2) 断层面(近垂直平面 x≈1000) ----
    gp.add_surface_points(
        geo_model=geo_model,
        x=[1000, 1000, 1000],
        y=[500, 500, 500],
        z=[200, 500, 800],
        elements_names=["fault"] * 3,
    )

    # ---- 3) 产状:地层水平,断层法向量沿 +x ----
    gp.add_orientations(
        geo_model=geo_model,
        x=[400, 1600,   1000],
        y=[500, 500,    500],
        z=[700, 500,    500],
        elements_names=["top", "top", "fault"],
        pole_vector=[
            [0.0, 0.0, 1.0],   # 西盘水平
            [0.0, 0.0, 1.0],   # 东盘水平
            [1.0, 0.0, 0.0],   # 垂直断层,法向量 +x
        ],
    )

    # ---- 4) 标记断层关系 ----
    gp.set_is_fault(
        frame=geo_model.structural_frame,
        fault_groups=["Fault_Series"],
    )

    # ---- 5) 求解 ----
    gp.compute_model(geo_model)
    return geo_model


def main() -> None:
    geo_model = build_model()
    print(geo_model.structural_frame)

    gpv.plot_2d(geo_model, direction=["y"], show_data=True)
    out = save_2d_figure("03_fault_model")
    print(f"已保存 2D 截面: {out}")
    plt.close("all")

    gpv.plot_3d(geo_model, show_data=True, show_lith=True, image=False)


if __name__ == "__main__":
    main()
