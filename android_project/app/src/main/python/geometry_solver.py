# app/src/main/python/geometry_solver.py
# 纯端侧离线运行的几何定理形式化推导与符号求解引擎 (Chaquopy + SymPy 驱动)
import re
import json
import math
import sympy as sp

def normalize_text(text):
    if not text:
        return ""
    t = text.replace("：", ":").replace("＝", "=").replace("，", ",").replace("。", ".")
    t = t.replace("（", "(").replace("）", ")").replace("／", "/").replace("＋", "+").replace("－", "-")
    t = t.replace("度", "°").replace("‘", "'").replace("’", "'").replace("′", "'").replace("`", "'")
    t = t.replace("＜", "∠").replace("<", "∠").replace("L", "∠").replace("乙", "∠")
    t = t.replace("Rt\\Delta", "Rt△").replace("Rt\\triangle", "Rt△").replace("Rt A", "Rt△")
    t = t.replace("\\Delta", "△").replace("\\triangle", "△").replace("▲", "△")
    t = t.replace("∥", "//").replace("\\parallel", "//")
    t = t.replace("\\perp", "⊥")
    return t

def extract_facts(text):
    norm = normalize_text(text)
    facts = {
        "raw_text": text,
        "normalized": norm,
        "is_right_triangle": bool(re.search(r"Rt△|直角|90°|⊥|垂直|勾股", norm)),
        "is_isosceles": bool(re.search(r"等腰", norm)),
        "is_equilateral": bool(re.search(r"等边|正三角", norm)),
        "is_circle": bool(re.search(r"⊙|圆|半径|直径|弦|切线|垂径", norm)),
        "is_parallel": bool(re.search(r"//|平行", norm)),
        "is_similar": bool(re.search(r"相似|∽|对应边", norm)),
        "is_congruent": bool(re.search(r"全等|≌", norm)),
        "is_area": bool(re.search(r"面积", norm)),
        "is_perimeter": bool(re.search(r"周长", norm)),
        "lengths": {},
        "angles": {},
        "conditions_list": [],
        "target": None
    }

    # 提取求解目标
    target_match = re.search(r"(?:求|则|计算|求出|那么)\s*([A-Za-z0-9'∠△⊙\u4e00-\u9fa5]+?)(?:的|长|度数|大小|值|面积|周长|$|\s|,|\.)", norm)
    if target_match:
        facts["target"] = target_match.group(1).strip()

    # 提取线段长
    length_matches = re.findall(r"(?:(半径|直径|弦长?|高|底边?|边长|[A-Z]{2}|[a-c]))(?:[rR])?\s*[=为是]\s*(\d+(?:\.\d+)?)", norm)
    for k, v in length_matches:
        facts["lengths"][k] = float(v)
        facts["conditions_list"].append(f"线段 {k} = {v}")

    # 提取角度
    angle_matches = re.findall(r"(?:∠|角)\s*([A-Z]{1,3}|\d+)\s*[=为是]\s*(\d+(?:\.\d+)?)", norm)
    for k, v in angle_matches:
        facts["angles"][k] = float(v)
        facts["conditions_list"].append(f"角 ∠{k} = {v}°")

    # 提取所有正数值备用
    facts["numbers"] = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", norm) if float(x) > 0]
    return facts

def solve_geometry(ocr_text):
    if not ocr_text or not ocr_text.strip():
        return json.dumps({
            "problem_type": "未输入题目",
            "theorems_used": [],
            "identified_conditions": [],
            "steps": ["请先拍摄或选择包含几何题目的照片，或者在文本框中输入题目。"],
            "final_answer": "等待输入"
        }, ensure_ascii=False)

    facts = extract_facts(ocr_text)
    norm = facts["normalized"]
    conditions = facts["conditions_list"]
    target = facts["target"] or "目标量"

    # ==================== 1. 圆与垂径定理 / 圆周角定理 ====================
    if facts["is_circle"]:
        r = facts["lengths"].get("半径") or facts["lengths"].get("r")
        chord = facts["lengths"].get("弦") or facts["lengths"].get("弦长") or facts["lengths"].get("AB")
        angles = facts["angles"]
        
        # 垂径定理: r² = d² + (chord/2)²
        if (r and chord) or (facts["numbers"] and len(facts["numbers"]) >= 2 and ("弦" in norm or "垂径" in norm)):
            if not r:
                r = max(facts["numbers"][0], facts["numbers"][1])
                chord = min(facts["numbers"][0], facts["numbers"][1])
            half_c = chord / 2
            d_sq = r**2 - half_c**2
            if d_sq >= 0:
                d_val = math.sqrt(d_sq)
                return json.dumps({
                    "problem_type": "圆与垂径定理计算",
                    "identified_conditions": [f"半径 r = {r}", f"弦长 = {chord}", "垂径垂直平分弦"],
                    "theorems_used": ["垂径定理: 垂直于弦的直径平分这条弦", "勾股定理: r² = d² + (l/2)²"],
                    "steps": [
                        f"1. 提取已知圆要素: 半径 r = {r}, 弦长 = {chord}",
                        f"2. 应用【垂径定理】: 垂直于弦的半径平分该弦，半弦长 = {chord} / 2 = {half_c}",
                        f"3. 在圆心、弦中点、弦端点构成的 Rt△ 中应用【勾股定理】: r² = d² + (半弦长)²",
                        f"4. 代入数据求解弦心距: d = √(r² - {half_c}²) = √({r}² - {half_c}²) = √({d_sq:.2f}) = {d_val:.2f}"
                    ],
                    "final_answer": f"圆心到弦的距离 (弦心距) = {d_val:.2f}"
                }, ensure_ascii=False)

        # 圆心角与圆周角定理: 同弧所对圆心角是圆周角的2倍
        if len(angles) >= 1:
            ang_name, ang_val = list(angles.items())[0]
            if "圆周角" in norm:
                circum_ang = ang_val / 2
                return json.dumps({
                    "problem_type": "圆心角与圆周角定理推导",
                    "identified_conditions": [f"已知角 ∠{ang_name} = {ang_val}°", "同弧所对角"],
                    "theorems_used": ["圆周角定理: 一条弧所对的圆周角等于它所对的圆心角的一半"],
                    "steps": [
                        f"1. 已知同弧所对圆心角: ∠{ang_name} = {ang_val}°",
                        f"2. 应用【圆周角定理】: 在同圆或等圆中，同弧所对的圆周角等于圆心角的一半",
                        f"3. 计算得圆周角: {target} = {ang_val}° / 2 = {circum_ang:.1f}°"
                    ],
                    "final_answer": f"圆周角 = {circum_ang:.1f}°"
                }, ensure_ascii=False)

    # ==================== 2. 直角三角形 (勾股定理与特殊角) ====================
    if facts["is_right_triangle"] or any(v == 90 for v in facts["angles"].values()):
        lengths = facts["lengths"]
        angles = facts["angles"]

        # 含 30° 角直角三角形: 30° 角所对直角边是斜边一半
        special_30 = [k for k, v in angles.items() if v == 30]
        if special_30 and lengths:
            side_k, side_v = list(lengths.items())[0]
            if "斜边" in norm or "AB" in target:
                hyp = side_v * 2
                return json.dumps({
                    "problem_type": "含30°特殊角直角三角形性质",
                    "identified_conditions": [f"Rt△ 中 ∠{special_30[0]} = 30°", f"直角边 {side_k} = {side_v}"],
                    "theorems_used": ["直角三角形性质定理: 30° 角所对的直角边等于斜边的一半 (比例 1 : √3 : 2)"],
                    "steps": [
                        f"1. 识别条件: 在 Rt△ 中存在 30° 特殊角，已知直角边 {side_k} = {side_v}",
                        f"2. 应用【30° 角性质】: 30° 对边 = 斜边 / 2",
                        f"3. 推导斜边长: 斜边 = 2 × {side_k} = 2 × {side_v} = {hyp:.2f}"
                    ],
                    "final_answer": f"斜边 {target} = {hyp:.2f}"
                }, ensure_ascii=False)

        # 勾股定理求解
        if len(lengths) >= 2 or len(facts["numbers"]) >= 2:
            nums = list(lengths.values()) if len(lengths) >= 2 else facts["numbers"][:2]
            n1, n2 = nums[0], nums[1]
            max_n, min_n = max(n1, n2), min(n1, n2)

            # 判断求斜边还是求直角边
            if "斜边" in norm or "c" in target.lower():
                hyp = math.sqrt(n1**2 + n2**2)
                return json.dumps({
                    "problem_type": "直角三角形勾股定理 (求斜边)",
                    "identified_conditions": [f"直角边 a = {n1}", f"直角边 b = {n2}"],
                    "theorems_used": ["勾股定理: a² + b² = c² (两直角边平方和等于斜边平方)"],
                    "steps": [
                        f"1. 确认两直角边长: a = {n1}, b = {n2}",
                        f"2. 应用【勾股定理】: 斜边 c = √(a² + b²)",
                        f"3. 代入计算: c = √({n1}² + {n2}²) = √({n1**2 + n2**2:.2f}) = {hyp:.2f}"
                    ],
                    "final_answer": f"斜边 {target} = {hyp:.2f}"
                }, ensure_ascii=False)
            else:
                # 默认最大边为斜边，求另一直角边
                leg_sq = max_n**2 - min_n**2
                leg = math.sqrt(leg_sq)
                return json.dumps({
                    "problem_type": "直角三角形勾股定理 (求直角边)",
                    "identified_conditions": [f"斜边 = {max_n}", f"已知直角边 = {min_n}"],
                    "theorems_used": ["勾股定理: a² + b² = c²  =>  b = √(c² - a²)"],
                    "steps": [
                        f"1. 确认已知边: 斜边 = {max_n}, 直角边 = {min_n}",
                        f"2. 应用【勾股定理】: 直角边 = √(斜边² - 直角边²)",
                        f"3. 代入计算: {target} = √({max_n}² - {min_n}²) = √({max_n**2 - min_n**2:.2f}) = {leg:.2f}"
                    ],
                    "final_answer": f"直角边 {target} = {leg:.2f}"
                }, ensure_ascii=False)

    # ==================== 3. 等边三角形几何计算 ====================
    if facts["is_equilateral"]:
        side = None
        for k in ["边长", "a", "AB", "BC", "AC"]:
            if k in facts["lengths"]:
                side = facts["lengths"][k]
                break
        if side is None and facts["numbers"]:
            side = facts["numbers"][0]

        if side:
            area = (math.sqrt(3) / 4) * (side ** 2)
            height = (math.sqrt(3) / 2) * side
            perimeter = 3 * side
            return json.dumps({
                "problem_type": "等边三角形几何计算",
                "identified_conditions": [f"等边三角形边长 a = {side}"],
                "theorems_used": ["等边三角形性质: 三边相等，内角均为 60°", "面积公式: S = (√3/4)·a²", "高公式: h = (√3/2)·a"],
                "steps": [
                    f"1. 识别等边三角形边长: a = {side}",
                    f"2. 应用【等边三角形高公式】: h = (√3 / 2) · a = (√3 / 2) × {side} = {height:.2f}",
                    f"3. 应用【等边三角形面积公式】: S = (√3 / 4) · a² = (√3 / 4) × {side}² = {area:.2f}",
                    f"4. 周长计算: C = 3a = 3 × {side} = {perimeter:.2f}"
                ],
                "final_answer": f"面积 S = {area:.2f}, 高 h = {height:.2f}, 周长 = {perimeter:.2f}"
            }, ensure_ascii=False)

    # ==================== 4. 等腰三角形角度推导 ====================
    if facts["is_isosceles"] and facts["angles"]:
        ang_name, ang_val = list(facts["angles"].items())[0]
        if "顶角" in norm or ang_val >= 90:
            base_ang = (180 - ang_val) / 2
            return json.dumps({
                "problem_type": "等腰三角形角度推导 (已知顶角)",
                "identified_conditions": [f"等腰△ 顶角 ∠{ang_name} = {ang_val}°"],
                "theorems_used": ["等腰三角形性质: 等边对等角 (两底角相等)", "三角形内角和定理: 三内角和为 180°"],
                "steps": [
                    f"1. 确认等腰三角形顶角: ∠{ang_name} = {ang_val}°",
                    f"2. 根据【等边对等角】定理，两底角相等",
                    f"3. 根据【内角和定理】: 顶角 + 2 × 底角 = 180°",
                    f"4. 计算底角: 底角 = (180° - {ang_val}°) / 2 = {base_ang:.1f}°"
                ],
                "final_answer": f"底角 = {base_ang:.1f}°"
            }, ensure_ascii=False)
        else:
            vertex_ang = 180 - 2 * ang_val
            return json.dumps({
                "problem_type": "等腰三角形角度推导 (已知底角)",
                "identified_conditions": [f"等腰△ 底角 ∠{ang_name} = {ang_val}°"],
                "theorems_used": ["等腰三角形性质: 等边对等角", "三角形内角和定理: 三内角和为 180°"],
                "steps": [
                    f"1. 确认等腰三角形底角: ∠{ang_name} = {ang_val}°",
                    f"2. 由性质得另一底角也为 {ang_val}°",
                    f"3. 顶角计算: 顶角 = 180° - 2 × {ang_val}° = {vertex_ang:.1f}°"
                ],
                "final_answer": f"顶角 = {vertex_ang:.1f}°"
            }, ensure_ascii=False)

    # ==================== 5. 三角形内角和定理与外角性质 ====================
    if len(facts["angles"]) >= 2:
        items = list(facts["angles"].items())
        a1_name, a1_val = items[0]
        a2_name, a2_val = items[1]
        a3_val = 180 - a1_val - a2_val
        return json.dumps({
            "problem_type": "三角形内角和定理角度推导",
            "identified_conditions": [f"∠{a1_name} = {a1_val}°", f"∠{a2_name} = {a2_val}°"],
            "theorems_used": ["三角形内角和定理: 三角形三个内角之和恒等于 180° (∠A + ∠B + ∠C = 180°)"],
            "steps": [
                f"1. 提取已知角: ∠{a1_name} = {a1_val}°, ∠{a2_name} = {a2_val}°",
                f"2. 应用【三角形内角和定理】: ∠A + ∠B + ∠C = 180°",
                f"3. 推导第三角: {target} = 180° - ∠{a1_name} - ∠{a2_name} = 180° - {a1_val}° - {a2_val}° = {a3_val:.1f}°"
            ],
            "final_answer": f"{target} = {a3_val:.1f}°"
        }, ensure_ascii=False)

    # ==================== 6. 平行线性质定理 ====================
    if facts["is_parallel"] and facts["angles"]:
        ang_name, ang_val = list(facts["angles"].items())[0]
        supp = 180 - ang_val
        return json.dumps({
            "problem_type": "平行线性质定理推导",
            "identified_conditions": [f"两直线平行", f"已知角 ∠{ang_name} = {ang_val}°"],
            "theorems_used": ["两直线平行，同位角相等", "两直线平行，内错角相等", "两直线平行，同旁内角互补"],
            "steps": [
                f"1. 确认平行关系与已知角: 直线平行，∠{ang_name} = {ang_val}°",
                f"2. 应用【平行线性质】定理:",
                f"   • 同位角 / 内错角 = {ang_val}°",
                f"   • 同旁内角 = 180° - {ang_val}° = {supp:.1f}°"
            ],
            "final_answer": f"同位角/内错角 = {ang_val}°, 同旁内角 = {supp:.1f}°"
        }, ensure_ascii=False)

    # ==================== 7. 海伦公式 (三边求面积) ====================
    if len(facts["lengths"]) >= 3 or (len(facts["numbers"]) >= 3 and facts["is_area"]):
        nums = list(facts["lengths"].values()) if len(facts["lengths"]) >= 3 else facts["numbers"][:3]
        a, b, c = nums[0], nums[1], nums[2]
        if a + b > c and a + c > b and b + c > a:
            p = (a + b + c) / 2
            area = math.sqrt(p * (p - a) * (p - b) * (p - c))
            return json.dumps({
                "problem_type": "三角形三边求面积 (海伦公式)",
                "identified_conditions": [f"三边长 a = {a}", f"b = {b}", f"c = {c}"],
                "theorems_used": ["海伦公式 (Heron's Formula): S = √(p(p-a)(p-b)(p-c)), 其中 p = (a+b+c)/2"],
                "steps": [
                    f"1. 验证三角形三边关系: {a} + {b} > {c} (构成有效三角形)",
                    f"2. 计算半周长: p = ({a} + {b} + {c}) / 2 = {p:.2f}",
                    f"3. 应用【海伦公式】代入计算: S = √({p:.2f} × {p-a:.2f} × {p-b:.2f} × {p-c:.2f}) = {area:.2f}"
                ],
                "final_answer": f"三角形面积 S = {area:.2f}"
            }, ensure_ascii=False)

    # ==================== 8. 通用符号代数方程求解 (SymPy) ====================
    eq_matches = re.findall(r"([a-zA-Z0-9\+\-\*\/\s]+=[a-zA-Z0-9\+\-\*\/\s]+)", norm)
    if eq_matches:
        try:
            steps = ["1. 从题目文本中提取几何代数方程:"]
            eqs = []
            for m in eq_matches:
                parts = m.split("=")
                left_expr = sp.sympify(parts[0])
                right_expr = sp.sympify(parts[1])
                eq = sp.Eq(left_expr, right_expr)
                eqs.append(eq)
                steps.append(f"   • 方程: {eq}")
            sol = sp.solve(eqs)
            steps.append(f"2. 应用 SymPy 符号代数求解器消元求解")
            return json.dumps({
                "problem_type": "几何代数方程组符号求解",
                "identified_conditions": [str(eq) for eq in eqs],
                "theorems_used": ["代数方程组消元求解"],
                "steps": steps,
                "final_answer": f"解得: {sol}"
            }, ensure_ascii=False)
        except Exception:
            pass

    # ==================== 9. 通用双数值几何关系推导 ====================
    if len(facts["numbers"]) >= 2:
        n1, n2 = facts["numbers"][0], facts["numbers"][1]
        c = math.sqrt(n1**2 + n2**2)
        diff_sq = abs(n1**2 - n2**2)
        leg = math.sqrt(diff_sq) if diff_sq > 0 else 0
        return json.dumps({
            "problem_type": "通用几何数值推导",
            "identified_conditions": [f"提取数值 1: {n1}", f"提取数值 2: {n2}"],
            "theorems_used": ["勾股定理 / 比例几何定理"],
            "steps": [
                f"1. 提取题目关键数值: {n1}, {n2}",
                f"2. 若两数为直角边，则【勾股斜边】: c = √({n1}² + {n2}²) = {c:.2f}",
                f"3. 若较大量为斜边，则【直角边】: b = √({max(n1,n2)}² - {min(n1,n2)}²) = {leg:.2f}"
            ],
            "final_answer": f"可能斜边长: {c:.2f} | 直角边长: {leg:.2f}"
        }, ensure_ascii=False)

    # 无法推导时返回清晰指导
    return json.dumps({
        "problem_type": "未能识别出明确已知量",
        "identified_conditions": [],
        "theorems_used": [],
        "steps": [
            "1. OCR 已成功识别文字，但题目中的关键数字或几何关系不够明确。",
            "2. 建议：您可以在上方的题目文本框中直接编辑/补充已知条件（例如加上 'AB=5, BC=12, ∠C=90°'），然后点击下方【立即推导求解】。"
        ],
        "final_answer": "请补充或微调题目文本"
    }, ensure_ascii=False)

# 兼容别名
auto_parse_and_solve = solve_geometry
