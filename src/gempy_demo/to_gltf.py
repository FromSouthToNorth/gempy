"""把 GemPy 计算出的地层/断层面导出为 glTF/GLB。

数据流:
    geo_model.solutions.dc_meshes[i].vertices/edges    # 由 dual contouring 生成的三角网
    → input_transform.apply_inverse                     # 还原到 extent 坐标(否则坐标被内部归一化)
    → trimesh.Scene + 每个 element 一个 Trimesh         # 保留 element 的颜色
    → scene.export("xxx.glb", file_type="glb")          # 单文件二进制 GLB

注意:dc_meshes 的 vertices 是 GemPy 内部归一化坐标,直接用会得到一个怪比例的模型,
    必须用 geo_model.input_transform.apply_inverse 还原。
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple

import numpy as np

from .utils import ensure_output_dir


def _hex_to_rgba(hex_color: str | None, alpha: int = 255) -> tuple[int, int, int, int]:
    h = (hex_color or "#cccccc").lstrip("#")
    if len(h) != 6:
        return (200, 200, 200, alpha)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _flatten_elements(geo_model) -> list:
    out = []
    for grp in geo_model.structural_frame.structural_groups:
        out.extend(grp.elements)
    return out


def iter_surface_meshes(
    geo_model,
) -> Iterator[Tuple[str, str, np.ndarray, np.ndarray]]:
    """yield (name, color_hex, vertices_xyz, faces_ijk),坐标已还原到原 extent。"""
    sols = geo_model.solutions
    if sols is None or getattr(sols, "dc_meshes", None) is None:
        raise RuntimeError("geo_model 没有解。请先调用 gp.compute_model(geo_model)。")

    inv = geo_model.input_transform.apply_inverse
    elements = _flatten_elements(geo_model)

    for el, dc in zip(elements, sols.dc_meshes):
        if dc is None:
            continue
        verts = np.asarray(dc.vertices, dtype=np.float64)
        faces = np.asarray(dc.edges, dtype=np.int64)
        if verts.size == 0 or faces.size == 0:
            continue
        verts = inv(verts)
        yield el.name, el.color, verts, faces


def export_glb(geo_model, name: str, *, alpha: int = 255) -> Path:
    """把所有 surface 写入单个二进制 GLB,返回路径。需要 `trimesh`。"""
    import trimesh

    scene = trimesh.Scene()
    n = 0
    for surf, color, verts, faces in iter_surface_meshes(geo_model):
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        mesh.visual.face_colors = _hex_to_rgba(color, alpha)
        scene.add_geometry(mesh, node_name=surf, geom_name=surf)
        n += 1
    if n == 0:
        raise RuntimeError("没有可导出的 surface mesh。检查 compute_model 是否成功。")

    out = ensure_output_dir() / f"{name}.glb"
    scene.export(str(out), file_type="glb")
    return out


def export_gltf_via_pyvista(geo_model, name: str) -> Path:
    """备选:用 PyVista off-screen Plotter 输出 .gltf + .bin。

    输出文本 .gltf,加载时同目录的 .bin 必须一起放置。
    适合不想装 trimesh 的场景。
    """
    import pyvista as pv

    pl = pv.Plotter(off_screen=True)
    for surf, color, verts, faces in iter_surface_meshes(geo_model):
        n_faces = len(faces)
        pv_faces = np.empty((n_faces, 4), dtype=np.int64)
        pv_faces[:, 0] = 3
        pv_faces[:, 1:] = faces
        poly = pv.PolyData(verts, pv_faces.ravel())
        pl.add_mesh(poly, color=color, name=surf)

    out = ensure_output_dir() / f"{name}.gltf"
    pl.export_gltf(str(out))
    pl.close()
    return out
