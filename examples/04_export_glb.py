"""04 — 把任一示例的 GemPy 模型导出为 GLB,可在 CesiumJS 中作为 Model 加载。

用法:
    python examples/04_export_glb.py            # 导出全部 3 个示例
    python examples/04_export_glb.py 03         # 仅导出 03_fault_model

依赖:
    pip install trimesh        # 单文件 GLB 路径(默认)
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parents[0] / "src"))
sys.path.insert(0, str(THIS_DIR))

from gempy_demo.to_gltf import export_glb

EXAMPLES = {
    "01": ("01_basic_horizontal_layers", "01_basic_horizontal", False),
    "02": ("02_anticline", "02_anticline", False),
    "03": ("03_fault_model", "03_fault_model", False),
    "05": ("05_alesmodel", "05_alesmodel", True),
}


def main() -> None:
    keys = sys.argv[1:] or list(EXAMPLES)
    for k in keys:
        if k not in EXAMPLES:
            print(f"未知示例 '{k}',可选: {list(EXAMPLES)}")
            continue
        mod_name, out_name, center = EXAMPLES[k]
        print(f"[{k}] 构建 {mod_name} ...")
        mod = importlib.import_module(mod_name)
        geo_model = mod.build_model()
        out = export_glb(geo_model, out_name, center_to_origin=center)
        print(f"[{k}] 已写入 {out}")


if __name__ == "__main__":
    main()
