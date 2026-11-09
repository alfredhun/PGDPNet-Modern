# Modernized PGDPNet: End-to-End Plane Geometry Diagram & Problem Parsing Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![PyTorch 2.x](https://img.shields.io/badge/PyTorch-2.x%20compatible-orange.svg)](https://pytorch.org/)
[![No C++ Compiler Required](https://img.shields.io/badge/C%2B%2B%20Build-Zero%20Dependency-green.svg)](#modernization-highlights)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An industrial-grade, fully modernized neuro-symbolic system for **Plane Geometry Diagram Parsing (PGDP)** and multi-modal mathematical problem analysis. 

Based on the CVPR/IJCAI work *[Plane Geometry Diagram Parsing (PGDPNet)](https://arxiv.org/abs/2205.09363)*, this repository has been comprehensively refactored to work out-of-the-box on modern OS platforms (Windows, Linux, macOS) without requiring legacy CUDA toolchains, Visual Studio C++ compilers, or outdated DGL builds.

---

## 🌟 Key Modernization Highlights (重构亮点)

1. **Zero C++ Compilation Barrier (零 C++ 编译门槛)**:
   - Replaced all custom C++/CUDA extensions in `geo_parse._C` (`nms.cpp`, `roi_align.cpp`, `roi_pool.cpp`, `sigmoid_focal_loss.cpp`, `deform_conv.cpp`) with official, highly optimized `torchvision.ops` native operators.
   - Installs cleanly across Windows, Linux, and macOS via pure-python `pip install -e .`.

2. **DGL Graph Library Decoupled (解耦脆弱的旧版 DGL)**:
   - Replaced the brittle legacy `dgl-cuda10.1==0.6.1` dependency with a pure-PyTorch matrix-based Graph Attention Network (`SimpleGraph` + `PureTorchGAT`).

3. **Modern PyTorch 2.x & Python 3.10~3.12 Ready**:
   - Eliminated deprecated `torch._six` imports, replaced with standard `importlib`.
   - Fixed PyTorch 2.x gradient detached numpy conversions and dynamic shape dimension constraints.
   - Added device-agnostic `.to(device)` handling (CPU, NVIDIA CUDA, Apple MPS).

4. **Multi-Modal Visual-Topology Pipeline Integration**:
   - Integrates formal predicate extraction (`PointLiesOnLine`, `Perpendicular`, `Parallel`, `IntersectionPoint`) compliant with the **PGDP5K** & **Inter-GPS** formal language specifications.
   - Handles multi-subfigure evolution (e.g., Subfigure 1, 2, 3), coordinate geometry, and kinematics function travel graphs.

---

## 📂 Project Structure (项目目录结构)

```
.
├── PGDP/                      # Modernized PGDPNet core deep learning engine
│   ├── configs/               # FPN, MobileNetV2, and GNN configurations
│   ├── demo/                  # Official demo images & ground-truth logic forms
│   ├── geo_parse/             # Pure Python/Torchvision neural network modules
│   └── setup.py               # Modernized pure-python package installer
│
├── app_config.py              # Configuration manager for LLM/VLM APIs
├── geometry_engine.py         # Multi-modal formal geometry diagram extractor
├── fusion_pipeline.py         # End-to-end question OCR + diagram topology fusion
├── run_diagram_pipeline.py    # Complete execution script (PGDPNet backbone + formal parser)
├── test_forward.py            # Automated PyTorch forward pass unit test
└── requirements.txt           # Modern dependencies
```

---

## 🚀 Quick Start (快速开始)

### 1. Environment Setup (环境配置)

```bash
git clone https://github.com/alfredhun/PGDPNet-Modern.git
cd PGDPNet-Modern

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

# Install modern PyTorch and Torchvision
pip install torch torchvision

# Install modernized geo_parse in editable mode
pip install -e ./PGDP

# Install auxiliary utilities
pip install openai opencv-python pillow numpy sympy shapely yacs tqdm
```

### 2. Verify Local PGDPNet Forward Inference (验证本地网络前向推理)

```bash
python test_forward.py
```
Outputs:
```
>>> 1. 正在构建现代化重构后的 PGDPNet 模型结构...
   -> 模型参数量: 5,464,933
>>> 2. 读取真实几何测试图片 (106.png)...
>>> 3. 在现代 PyTorch 2.x 环境下执行端到端前向推理...
>>> [CONGRATULATIONS!] PGDPNet 前向推理在现代 PyTorch 2.x 下全线跑通！
```

### 3. Parse Geometry Diagram to Formal Logic Forms (图元与形式化逻辑提取)

Configure your API key (optional for VLM fusion):
```powershell
$env:ZHIPUAI_API_KEY="your_api_key_here"
```

Run diagram parsing:
```bash
python run_diagram_pipeline.py
```

Sample output (`parse_result.json`):
```json
{
  "points": ["O", "C", "A", "B", "A'"],
  "collinear_groups": [
    ["O", "C", "A", "B"]
  ],
  "lines": [
    { "endpoints": ["O", "B"], "style": "solid_and_dashed" },
    { "endpoints": ["O", "A'"], "style": "dashed" },
    { "endpoints": ["A'", "C"], "style": "dashed" }
  ],
  "visual_symbols": {
    "right_angles": [
      { "vertex": "C", "arms": ["A'C", "OC"] }
    ],
    "explicit_values": []
  },
  "diagram_logic_forms": [
    "PointLiesOnLine(C, Line(O, B))",
    "PointLiesOnLine(A, Line(O, B))",
    "Perpendicular(Line(A', C), Line(O, B))"
  ]
}
```

---

## 📜 Citation & Credits (致谢与引用)

This repository is built on top of the original academic contributions:

- **PGDPNet / PGDP5K (IJCAI 2022 / CVPR 2022)**:
  ```bibtex
  @inproceedings{Zhang2022,
    title     = {Plane Geometry Diagram Parsing},
    author    = {Zhang, Ming-Liang and Yin, Fei and Hao, Yi-Han and Liu, Cheng-Lin},
    booktitle = {Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence, {IJCAI-22}},
    pages     = {1636--1643},
    year      = {2022}
  }
  ```
- **Inter-GPS (ACL 2021)** for formal diagram predicate conventions.

---

## 📄 License
This refactored project is licensed under the Apache 2.0 / MIT License.
