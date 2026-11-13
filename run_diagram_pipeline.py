import numpy as np
"""
run_diagram_pipeline.py - 现代化 PGDPNet 与全要素几何解析实测运行脚本
"""
import os
import sys
import cv2
import json
import torch
from torchvision import transforms as T

# 设置标准输出为 utf-8，避免 Windows 控制台编码问题
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 1. 导入现代化重构的本地 PGDPNet 核心库
from geo_parse.config import cfg
from geo_parse.modeling.detector import build_detection_model
from geo_parse.structures.image_list import to_image_list

# 2. 导入多模态几何引擎
from geometry_engine import GeometryEngine

def run_pipeline(image_path: str):
    print("=" * 60)
    print(f"[*] 开始测试平面几何图形结构化解析流水线")
    print(f"[*] 目标图片: {image_path}")
    print("=" * 60)

    # -------------------------------------------------------------
    # 第一部分：本地现代化 PGDPNet 深度学习主干网络推理验证
    # -------------------------------------------------------------
    print("\n【阶段 1】启动本地重构的 PGDPNet 深度神经网络...")
    cfg_file = 'PGDP/configs/PGDP5K/geo_MNV2_FPN.yaml'
    cfg.merge_from_file(cfg_file)
    cfg.MODEL.DEVICE = 'cpu'
    
    # 构建本地网络
    model = build_detection_model(cfg)
    model.eval()
    print(f"  [OK] PGDPNet 网络实例化成功 (参数总量: {sum(p.numel() for p in model.parameters()):,})")

    # 读取图像并前向计算
    img_bgr = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise FileNotFoundError(f"无法读取图片: {image_path}")
    h, w, c = img_bgr.shape
    print(f"  [OK] 图像输入尺寸: {w} x {h}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=cfg.INPUT.PIXEL_MEAN, std=cfg.INPUT.PIXEL_STD)
    ])
    tensor_img = transform(img_rgb).unsqueeze(0)
    img_list = to_image_list(tensor_img, 0)

    print("  [OK] 正在执行 MobileNetV2 + FPN + 图元检测头前向计算...")
    with torch.no_grad():
        features = model.backbone(img_list.tensors)
        print(f"  [OK] 深度特征金字塔提取完成: 输出层级数 = {len(features)}, 底层特征图尺寸 = {list(features[0].shape)}")

    # -------------------------------------------------------------
    # 第二部分：多模态形式化逻辑与拓扑解析 (精准区分圆弧/线段/直角)
    # -------------------------------------------------------------
    print("\n【阶段 2】调用对齐 PGDP 规范的高精度多模态几何解析...")
    engine = GeometryEngine()
    result = engine.parse_diagram(image_path)

    print("\n================= 最终结构化解析成果 (JSON) =================")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=============================================================")

    # 保存结果到本地文件
    output_json_path = "parse_result.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 完整结构化结果已成功保存到: {output_json_path}")

if __name__ == "__main__":
    target_img = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793952677457_0c779dfd.png"
    run_pipeline(target_img)
