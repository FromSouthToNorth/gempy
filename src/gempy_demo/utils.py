"""共享工具:输出目录管理 + matplotlib 图片导出。"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def save_2d_figure(name: str, dpi: int = 150) -> Path:
    """将当前 matplotlib figure 写入 output/{name}.png 并返回路径。"""
    out = ensure_output_dir() / f"{name}.png"
    plt.gcf().savefig(out, dpi=dpi, bbox_inches="tight")
    return out
