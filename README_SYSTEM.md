# 平面几何图形与试题结构化解析系统 (基于 PGDP 规范 + 智谱在线视觉模型)

## 一、 当前项目目录结构

```
F:\测试\
│
├── PGDP\                      # 官方 PGDP (Plane Geometry Diagram Parsing, IJCAI 2022) 源码仓库
│   ├── configs\               # 官方 FPN / GNN 配置文件
│   ├── demo\demo_images\      # 官方标准测试几何图片 (如 106.png, 70.png 等)
│   ├── geo_parse\             # 官方模型与图网络定义
│   └── text_content_gt.json   # 官方 PGDP5K 标注真值示例
│
├── venv\                      # 专用的 Python 虚拟运行环境
│
├── app_config.py              # 系统配置文件 (智谱 API Key 与端点配置)
├── geometry_engine.py         # 核心几何解析引擎 (输入纯几何图 -> 输出图元、符号及 diagram_logic_forms)
├── fusion_pipeline.py         # 端到端试题融合管线 (输入整道题图片 -> 输出题干 LaTeX + 几何拓扑逻辑融合 JSON)
└── test_connection.py         # 智谱 API 连通性测试脚本
```

## 二、 运行方式

### 1. 激活虚拟环境
```powershell
f:\测试\venv\Scripts\Activate.ps1
```

### 2. 解析纯几何图片 (对齐 PGDP 规范)
```bash
python geometry_engine.py
```
返回字段包含：
- `points`: 顶点列表
- `lines`: 线段列表
- `symbols`: 直角标注、平行箭头、相等刻度、角度标注、长度标注
- `diagram_logic_forms`: 形式化几何谓词 (如 `Perpendicular(...)`, `PointLiesOnLine(...)` 等)

### 3. 解析完整试题图片 (文字题干 + 公式 + 几何图)
```bash
python fusion_pipeline.py
```
返回字段包含：
- `question_text`: 带标准 LaTeX 公式与 Markdown 的完整题干
- `geometry_parsing`: 结构化图元与视觉标记
- `unified_logic_forms`: 融合了题干几何条件与图拓扑的形式化逻辑谓词
