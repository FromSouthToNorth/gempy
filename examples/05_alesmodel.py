"""
05 — Ales 模型(法国南部真实数据)

复现 GemPy 官方示例 examples/real/Alesmodel.py:从 CSV + DEM 直接构建一个
含 3 条断层、3 套地层的真实区域模型。

数据来源 (随仓库同步到 data/AlesModel/):
    2018_interf.csv                     接触点(geo coords + 形成层名)
    2018_orient_clust_n_init5_0.csv     产状(G_x/G_y/G_z + dip/azimuth)
    _cropped_DEM_coarse.tif             裁剪后的低分辨率 DEM(用作地形)

地层与断层 (从下到上,基底在最后):
    fault_left, fault_right, fault_lr   3 条独立断层
    Trias_Series : (TRIAS, LIAS)        三叠/侏罗
    Carbon_Series: CARBO                石炭
    Basement_Series: basement           基底

注意:
- 模型不太稳定,必须使用 float64;PyTorch 后端在 CPU 上即可,GPU 可选。
- refinement 设为 4 是为了示例快速跑通;论文图采用的是 6,可按需调高。
- 该示例 *不* 关闭 mesh_extraction,以便后续可被 04_export_glb.py 导出 GLB。
"""
from __future__ import annotations

import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import gempy as gp
import gempy_viewer as gpv
import matplotlib.pyplot as plt

from gempy_demo import save_2d_figure


DATA_DIR = PROJECT_ROOT / "data" / "AlesModel"
PATH_INTERF = DATA_DIR / "2018_interf.csv"
PATH_ORIENT = DATA_DIR / "2018_orient_clust_n_init5_0.csv"
PATH_DEM = DATA_DIR / "_cropped_DEM_coarse.tif"

EXTENT = [729550.0, 751500.0, 1913500.0, 1923650.0, -1800.0, 800.0]
CROP_EXTENT = [729550.0, 751500.0, 1913500.0, 1923650.0]


def build_model() -> gp.data.GeoModel:
    if not PATH_INTERF.exists():
        raise FileNotFoundError(
            f"找不到 {PATH_INTERF}\n"
            f"请确认 data/AlesModel/ 下已放置 2018_interf.csv 等数据文件。"
        )

    geo_model = gp.create_geomodel(
        project_name="Alesmodel",
        extent=EXTENT,
        resolution=None,
        refinement=4,
        importer_helper=gp.data.ImporterHelper(
            path_to_orientations=str(PATH_ORIENT),
            path_to_surface_points=str(PATH_INTERF),
        ),
    )

    # ---- 1) 地层栈映射:断层在前,沉积序列在后 ----
    gp.map_stack_to_surfaces(
        gempy_model=geo_model,
        mapping_object={
            "fault_left": "fault_left",
            "fault_right": "fault_right",
            "fault_lr": "fault_lr",
            "Trias_Series": ("TRIAS", "LIAS"),
            "Carbon_Series": "CARBO",
            "Basement_Series": "basement",
        },
        remove_unused_series=True,
    )

    # ---- 2) 给沉积层指定颜色(三色更易在 2D 切片中辨认) ----
    geo_model.structural_frame.get_element_by_name("LIAS").color = "#015482"
    geo_model.structural_frame.get_element_by_name("TRIAS").color = "#9f0052"
    geo_model.structural_frame.get_element_by_name("CARBO").color = "#ffbe00"

    # ---- 3) 把三组断层标为 fault(同时让 viewer 自动刷新颜色) ----
    gp.set_is_fault(
        frame=geo_model.structural_frame,
        fault_groups=[
            geo_model.structural_frame.get_group_by_name("fault_left"),
            geo_model.structural_frame.get_group_by_name("fault_right"),
            geo_model.structural_frame.get_group_by_name("fault_lr"),
        ],
        change_color=True,
    )

    # ---- 4) 截面网格:用于 plot_section_traces ----
    gp.set_section_grid(
        grid=geo_model.grid,
        section_dict={
            "section1": ([732000, 1916000], [745000, 1916000], [200, 150]),
        },
    )

    # ---- 5) 地形(DEM) ----
    if PATH_DEM.exists():
        gp.set_topography_from_file(
            grid=geo_model.grid,
            filepath=str(PATH_DEM),
            crop_to_extent=CROP_EXTENT,
        )

    # ---- 6) 数值稳定性微调 ----
    # 这是个不太稳定的真实模型,官方文档建议:
    #   * 减小 nugget 让接触点 / 产状的影响更柔和
    #   * range = 0.8 (而不是默认 1.0) 让插值核更紧
    #   * octree_error_threshold 调低,但 chunk_size 调小避免内存爆
    geo_model.interpolation_options.number_octree_levels_surface = 4
    geo_model.interpolation_options.kernel_options.range = 0.8
    gp.modify_surface_points(
        geo_model=geo_model,
        elements_names=["CARBO", "LIAS", "TRIAS"],
        nugget=0.005,
    )
    geo_model.interpolation_options.evaluation_options.octree_error_threshold = 0.5
    geo_model.interpolation_options.evaluation_options.evaluation_chunk_size = 50_000

    # ---- 7) 求解 ----
    # 必须 float64,否则会得到 NaN。GPU 不可用时退回 CPU。
    try:
        import torch
        use_gpu = torch.cuda.is_available()
    except ImportError:
        use_gpu = False

    gp.compute_model(
        geo_model,
        engine_config=gp.data.GemPyEngineConfig(
            backend=gp.data.AvailableBackends.PYTORCH,
            use_gpu=use_gpu,
            dtype="float64",
        ),
    )
    return geo_model


def main() -> None:
    geo_model = build_model()
    print(geo_model.structural_frame)

    # ---- 2D 截面(y 方向,中部) ----
    gpv.plot_2d(
        geo_model,
        cell_number=[4],
        direction=["y"],
        show_topography=True,
        show_data=True,
    )
    out = save_2d_figure("05_alesmodel_y_mid")
    print(f"已保存 2D 截面: {out}")
    plt.close("all")

    # ---- 2D 顶视图(沿 z 投影,显示地形 + 岩性) ----
    gpv.plot_2d(
        geo_model,
        section_names=["topography"],
        show_topography=False,
        show_lith=True,
    )
    out = save_2d_figure("05_alesmodel_top")
    print(f"已保存顶视图: {out}")
    plt.close("all")

    # ---- 3D 体可视化(带地形) ----
    gpv.plot_3d(
        geo_model,
        show_lith=True,
        show_topography=True,
        kwargs_plot_structured_grid={"opacity": 0.8},
        image=False,
    )


if __name__ == "__main__":
    main()
