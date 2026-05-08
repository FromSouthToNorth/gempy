"""
01 — 水平地层入门示例

最简单的 GemPy 模型:两层近乎水平的地层。
演示 GemPy 隐式建模的五步骤:
    1. 创建 GeoModel(范围 + 体素分辨率)
    2. 添加 surface points(地层接触面观测点)
    3. 添加 orientations(产状/法向量)
    4. compute_model 求解势场
    5. 2D 切片 + 3D 体可视化

注(GemPy v2025): element 必须在 structural_frame 中预先创建,
    否则 `add_surface_points` 会报 "Element not found"。
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
    """创建包含 surface1、surface2 两个 element 的结构框架。"""
    frame = gp.data.StructuralFrame.initialize_default_structure()
    # 默认已有 surface1,颜色保持不变
    frame.structural_groups[0].elements[0].color = "#FF5733"

    # 追加第二个地层 element
    empty_sp = np.array([], dtype=gp.data.SurfacePointsTable.dt)
    empty_or = np.array([], dtype=gp.data.OrientationsTable.dt)
    el = gp.data.StructuralElement(
        name="surface2",
        color="#33FF57",
        surface_points=gp.data.SurfacePointsTable(data=empty_sp),
        orientations=gp.data.OrientationsTable(data=empty_or),
    )
    frame.structural_groups[0].append_element(el)
    return frame


def build_model() -> gp.data.GeoModel:
    geo_model = gp.create_geomodel(
        project_name="basic_horizontal",
        extent=[0, 1000, 0, 1000, 0, 500],
        resolution=[50, 50, 50],
        refinement=4,
        structural_frame=_build_structural_frame(),
    )

    gp.add_surface_points(
        geo_model=geo_model,
        x=[100, 500, 900, 100, 500, 900],
        y=[500, 500, 500, 500, 500, 500],
        z=[400, 400, 400, 250, 250, 250],
        elements_names=[
            "surface1", "surface1", "surface1",
            "surface2", "surface2", "surface2",
        ],
    )

    gp.add_orientations(
        geo_model=geo_model,
        x=[500, 500],
        y=[500, 500],
        z=[400, 250],
        elements_names=["surface1", "surface2"],
        pole_vector=[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]],
    )

    gp.compute_model(geo_model)
    return geo_model


def main() -> None:
    geo_model = build_model()
    print(geo_model.structural_frame)

    gpv.plot_2d(geo_model, direction=["y"], show_data=True)
    out = save_2d_figure("01_basic_horizontal")
    print(f"已保存 2D 截面: {out}")
    plt.close("all")

    # 3D 体可视化(注释掉可避免弹窗)
    gpv.plot_3d(geo_model, show_data=True, show_lith=True, image=False)


if __name__ == "__main__":
    main()
