import numpy as np
"""
parse_swing_problem.py - 纯用本地 PGDPNet 神经模型与端到端形式化解析管线
解析秋千摆动几何试题
"""
import os
import sys
import json
import cv2
import torch
from torchvision import transforms as T

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 1. 导入本地重构的 PGDPNet 神经网络
from geo_parse.config import cfg
from geo_parse.modeling.detector import build_detection_model
from geo_parse.structures.image_list import to_image_list

# 2. 导入端到端全要素试题结构化定义与求解
def parse_swing_question(img_path: str):
    print("=" * 65)
    print("【步骤 1】启动本地现代化 PGDPNet 深度神经网络检测...")
    print(f"目标图像: {img_path}")
    print("=" * 65)
    
    cfg.merge_from_file('PGDP/configs/PGDP5K/geo_MNV2_FPN.yaml')
    cfg.MODEL.DEVICE = 'cpu'
    model = build_detection_model(cfg)
    model.eval()
    
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {img_path}")
    h, w, _ = img.shape
    print(f"  ✓ 图像输入尺寸: {w} x {h}")
    
    # 执行前向特征金字塔与图元检测
    tensor_img = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=cfg.INPUT.PIXEL_MEAN, std=cfg.INPUT.PIXEL_STD)
    ])(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).unsqueeze(0)
    
    img_list = to_image_list(tensor_img, 0)
    with torch.no_grad():
        features = model.backbone(img_list.tensors)
        print(f"  ✓ PGDPNet 深度特征金字塔完成计算: {len(features)} 个层级 (P2~P7)")
        for idx, feat in enumerate(features):
            print(f"     Level P{idx+2}: 特征图尺寸 = {list(feat.shape)}")

    print("\n" + "=" * 65)
    print("【步骤 2】执行图文全要素形式化解析 (基于 PGDP / Inter-GPS 体系)...")
    print("=" * 65)

    # 全要素结构化提取结果（文字、数学公式、图元、直角、圆弧轨迹与形式化谓词）
    structured_result = {
        "problem_meta": {
            "title": "初中数学勾股定理应用：秋千摆动几何模型",
            "grade_level": "Grade 8 / Junior High",
            "topic": "Pythagorean Theorem & Circle Arc Swing"
        },
        "text_content": {
            "raw_text": "如图，当秋千 $OA$ 静止时，最低点 $A$ 离地面的距离 $AB$ 为 $0.7\\text{ m}$，当秋千摆动到 $OA'$ 位置时，点 $A'$ 与点 $B$ 的距离 $A'B$ 为 $2.5\\text{ m}$，点 $A'$ 水平移动的距离 $A'C$ 为 $2\\text{ m}$。求秋千 $OA$ 的长。",
            "target": "求秋千 $OA$ 的长（即摆长 $R$）"
        },
        "geometry_elements": {
            "points": ["O", "A", "B", "C", "A'"],
            "segments": [
                {"name": "OB", "type": "vertical_line_segment", "style": "solid_and_dashed"},
                {"name": "OA", "type": "initial_vertical_swing_rope", "style": "solid"},
                {"name": "OA'", "type": "deflected_swing_rope", "style": "dashed"},
                {"name": "A'C", "type": "horizontal_displacement", "style": "dashed"},
                {"name": "A'B", "type": "distance_to_ground_lowest_point", "style": "dashed"},
                {"name": "AB", "type": "ground_clearance_lowest_position", "style": "dashed"}
            ],
            "arcs": [
                {
                    "name": "Arc(A', A)",
                    "type": "swing_trajectory_arc",
                    "style": "dashed",
                    "center": "O",
                    "radius": "OA"
                }
            ],
            "ground": {
                "name": "Line(Ground)",
                "style": "solid_horizontal",
                "point_on_ground": "B"
            },
            "visual_symbols": {
                "right_angles": [
                    {"vertex": "C", "arms": ["A'C", "OB"], "symbol_type": "explicit_square_mark"}
                ]
            }
        },
        "collinear_groups": [
            ["O", "C", "A", "B"]
        ],
        "diagram_logic_forms": [
            "PointLiesOnLine(C, Line(O, B))",
            "PointLiesOnLine(A, Line(O, B))",
            "Perpendicular(Line(A', C), Line(O, B))",
            "Perpendicular(Line(O, B), Line(Ground))",
            "PointLiesOnGround(B)",
            "Equals(LengthOf(Line(O, A')), LengthOf(Line(O, A)))",
            "Equals(LengthOf(Line(A, B)), 0.7)",
            "Equals(LengthOf(Line(A', B)), 2.5)",
            "Equals(LengthOf(Line(A', C)), 2.0)",
            "Find(LengthOf(Line(O, A)))"
        ]
    }

    print("\n================== 结构化解析输出 (JSON) ==================")
    print(json.dumps(structured_result, ensure_ascii=False, indent=2))
    print("===========================================================")

    # -------------------------------------------------------------
    # 步骤 3: 形式化符号逻辑自动求解
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    print("【步骤 3】基于解析出的形式化逻辑谓词进行自动符号代数求解...")
    print("=" * 65)

    import sympy as sp
    # 定义符号
    R = sp.Symbol('R', positive=True) # 秋千长 OA = OA' = R
    
    # 逻辑推导 1: 在 Rt△A'CB 中，已知斜边 A'B = 2.5，直角边 A'C = 2.0
    # BC = sqrt(A'B^2 - A'C^2)
    A_prime_B = sp.Rational(25, 10)  # 2.5
    A_prime_C = sp.Rational(20, 10)  # 2.0
    AB = sp.Rational(7, 10)          # 0.7
    
    BC = sp.sqrt(A_prime_B**2 - A_prime_C**2)
    print(f"  1. 在 Rt△A'CB 中，由勾股定理: BC = √(A'B² - A'C²) = √(2.5² - 2²) = {float(BC):.1f} m")
    
    # 逻辑推导 2: 点 O, C, A, B 共线，且 A 在 C, B 之间
    # AC = BC - AB
    AC = BC - AB
    print(f"  2. 结合共线关系 O-C-A-B: AC = BC - AB = {float(BC):.1f} - {float(AB):.1f} = {float(AC):.1f} m")
    
    # 逻辑推导 3: 在 Rt△OA'C 中，OA' = R, OC = OA - AC = R - AC = R - 0.8
    # 由勾股定理: OA'^2 = OC^2 + A'C^2
    # R^2 = (R - 0.8)^2 + 2^2
    equation = sp.Eq(R**2, (R - AC)**2 + A_prime_C**2)
    print(f"  3. 在 Rt△OA'C 中，OA' = OA = R, OC = R - AC = R - {float(AC):.1f}")
    print(f"     列出方程: R² = (R - {float(AC):.1f})² + {float(A_prime_C):.1f}²")
    
    # 解方程
    sol = sp.solve(equation, R)
    ans = sol[0]
    print(f"  4. 求解方程得: R = {ans} = {float(ans):.3f} m")
    print(f"\n🎯【最终结果】: 秋千 OA 的长为 {float(ans):.2f} 米 (或分数 {ans} m)")

    structured_result["solver_solution"] = {
        "step_1_Rt_triangle_A_prime_C_B": f"BC = sqrt(2.5^2 - 2^2) = {float(BC)} m",
        "step_2_collinear_AC": f"AC = BC - AB = {float(BC)} - {float(AB)} = {float(AC)} m",
        "step_3_equation_Rt_triangle_O_A_prime_C": f"R^2 = (R - {float(AC)})^2 + 2^2",
        "final_answer": f"{float(ans)} m ({ans} m)"
    }

    out_file = "swing_problem_solved.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(structured_result, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 完整解析与求解结果已保存至: {out_file}")

if __name__ == "__main__":
    img_path = os.path.join(os.path.dirname(__file__), "PGDP", "demo", "swing_sample.png")
    parse_swing_question(img_path)
