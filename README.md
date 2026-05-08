# GemPy 三维地质建模示例

基于 [GemPy v3](https://www.gempy.org/) 的隐式三维地质建模示例项目。GemPy 使用势场插值(基于 Lajaunie 1997)从地表点(surface points)和产状(orientations)推断地下结构。

## 项目结构

```
gempy/
├── requirements.txt      # 依赖列表
├── examples/             # 由浅入深的三个示例
│   ├── 01_basic_horizontal_layers.py   # 水平地层(入门)
│   ├── 02_anticline.py                 # 背斜构造
│   └── 03_fault_model.py               # 含正断层模型
├── src/gempy_demo/       # 公共工具函数
├── data/                 # 输入数据(CSV)
└── output/               # 渲染结果(图片/VTK)
```

## 安装

GemPy 依赖较重(包含 PyTorch / pyvista / VTK),建议使用独立虚拟环境:

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## 运行

```bash
python examples/01_basic_horizontal_layers.py
python examples/02_anticline.py
python examples/03_fault_model.py
```

每个示例会:
1. 在 `output/` 中保存 2D 截面图(`*.png`)
2. 弹出 PyVista 窗口显示 3D 体模型(可注释掉 `plot_3d`)

## GemPy 建模核心概念

| 概念 | 说明 |
|------|------|
| **GeoModel** | 模型容器,包含范围、分辨率、结构框架 |
| **Surface Points** | 地层接触面上的观测点(钻孔/露头) |
| **Orientations** | 产状测量(倾向/倾角,或法向量) |
| **Series** | 地层序列,定义沉积顺序 |
| **Fault** | 断层,作为独立 series 注入 |
| **Compute** | 调用 `compute_model` 求解势场,得到岩性体素 |

## GLB 导出与 Cesium 三维预览

### 导出 GLB

```bash
pip install -r requirements.txt   # 安装 trimesh
python examples/04_export_glb.py  # 导出全部 3 个模型为 output/*.glb
python examples/04_export_glb.py 03  # 仅导出 03_fault_model
```

导出的 GLB 包含每个 element 的 surface mesh 和原始颜色，坐标已通过 `input_transform.apply_inverse` 还原到模型 extent。

### Cesium 本地预览

```bash
cd output
python -m http.server 8080
```

浏览器打开 `http://localhost:8080/cesium_viewer.html`，填入真实经纬度高程后点击加载，模型即落在 OSM 底图上。

若要在自己的 Cesium 项目中加载：

```javascript
const modelMatrix = Cesium.Transforms.eastNorthUpToFixedFrame(
    Cesium.Cartesian3.fromDegrees(120.0, 31.0, 0)
);
const model = await Cesium.Model.fromGltfAsync({
    url: '03_fault_model.glb',
    modelMatrix: modelMatrix,
    scale: 1.0,
});
model.backFaceCulling = false;  // GemPy 三角网 winding order 不统一
viewer.scene.primitives.add(model);
```

## 参考

- 官方文档: https://docs.gempy.org/
- GitHub: https://github.com/gempy-project/gempy
- 论文: de la Varga et al., 2019, *GemPy 1.0: open-source stochastic geological modeling and inversion*
