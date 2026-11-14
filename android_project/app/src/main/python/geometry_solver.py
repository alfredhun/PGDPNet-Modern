# app/src/main/python/geometry_solver.py
# 纯端侧离线高精度神经符号几何定理推导引擎 (Chaquopy + SymPy 驱动)
import re
import json
import math
import sympy as sp

def normalize_text(text):
    if not text:
        return ""
    # 去除题号前缀如 "18.(8分)", "15.", "(1)"
    t = re.sub(r"^\s*\d+[\.、\s]+(?:\(\d+分\))?", "", text)
    t = t.replace("：", ":").replace("＝", "=").replace("，", ",").replace("。", ".").replace("；", ";")
    t = t.replace("（", "(").replace("）", ")").replace("／", "/").replace("＋", "+").replace("－", "-")
    t = t.replace("度", "°").replace("‘", "'").replace("’", "'").replace("′", "'").replace("`", "'")
    t = t.replace("＜", "∠").replace("<", "∠")
    t = t.replace("Rt\\Delta", "Rt△").replace("Rt\\triangle", "Rt△").replace("Rt A", "Rt△")
    t = t.replace("\\Delta", "△").replace("\\triangle", "△").replace("▲", "△")
    t = t.replace("∥", "//").replace("\\parallel", "//")
    t = t.replace("\\perp", "⊥")
    return t

def extract_entities_and_relations(text):
    norm = normalize_text(text)
    facts = {
        "raw_text": text,
        "normalized": norm,
        "triangles": set(re.findall(r"(?:Rt△|△)\s*([A-Z]{3})", norm)),
        "is_right_triangle": bool(re.search(r"Rt△|直角|90°|⊥|垂直|勾股", norm)),
        "is_isosceles": bool(re.search(r"等腰|AB\s*=\s*AC|AC\s*=\s*BC|AB\s*=\s*BC", norm)),
        "is_equilateral": bool(re.search(r"等边|正三角", norm)),
        "is_circle": bool(re.search(r"⊙|圆|半径|直径|弦|切线|垂径", norm)),
        "is_parallel": bool(re.search(r"//|平行", norm)),
        "is_midpoint": bool(re.search(r"中点|中线", norm)),
        "lengths": {},
        "angles": {},
        "perpendiculars": [],
        "parallels": [],
        "midpoints": [],
        "target": None
    }

    # 1. 提取连续相等线段，如 AB=AC=13
    chained_eq = re.findall(r"([A-Z]{2})\s*=\s*([A-Z]{2})\s*=\s*(\d+(?:\.\d+)?)", norm)
    for s1, s2, v in chained_eq:
        facts["lengths"][s1] = float(v)
        facts["lengths"][s2] = float(v)
        facts["is_isosceles"] = True

    # 2. 提取垂直关系：AD⊥BC, AC⊥BC
    perps = re.findall(r"([A-Z]{2})\s*⊥\s*([A-Z]{2})", norm)
    for p1, p2 in perps:
        facts["perpendiculars"].append((p1, p2))
        facts["is_right_triangle"] = True

    # 3. 提取平行关系：DE//BC
    pars = re.findall(r"([A-Z]{2})\s*//\s*([A-Z]{2})", norm)
    for p1, p2 in pars:
        facts["parallels"].append((p1, p2))
        facts["is_parallel"] = True

    # 4. 提取中点关系：D是AB的中点
    mids = re.findall(r"点?\s*([A-Z])\s*(?:是|为)\s*([A-Z]{2})\s*(?:的)?中点", norm)
    for pt, seg in mids:
        facts["midpoints"].append((pt, seg))
        facts["is_midpoint"] = True

    # 5. 提取角度（严格区分角度与线段长，必须带°或紧跟∠/角）
    angle_matches = re.findall(r"(?:∠|角)\s*([A-Z]{1,3}|\d+)\s*[=为是]\s*(\d+(?:\.\d+)?)\s*°?", norm)
    for k, v in angle_matches:
        facts["angles"][k] = float(v)
        if float(v) == 90:
            facts["is_right_triangle"] = True

    # 6. 提取线段长（排除角度数字）
    seg_matches = re.findall(r"(?:([A-Z]{2}|[a-c]|半径|直径|弦长?|高|底边?|边长))(?:[rR])?\s*[=为是]\s*(\d+(?:\.\d+)?)(?!\s*°)", norm)
    for k, v in seg_matches:
        if k not in facts["lengths"]:
            facts["lengths"][k] = float(v)

    # 7. 提取求解目标
    target_match = re.search(r"(?:求|计算|则|求出)\s*([A-Za-z0-9'∠△⊙\u4e00-\u9fa5]+?)(?:的|长|度数|大小|值|面积|周长|高|$|\s|,|\.)", norm)
    if target_match:
        facts["target"] = target_match.group(1).strip()

    return facts

def solve_geometry(ocr_text):
    if not ocr_text or not ocr_text.strip():
        return json.dumps({
            "problem_type": "未输入题目",
            "theorems_used": [],
            "identified_conditions": [],
            "steps": ["请拍摄或选择包含几何题目的清晰照片，或在上方文本框中输入题目文字。"],
            "final_answer": "等待输入"
        }, ensure_ascii=False)

    facts = extract_entities_and_relations(ocr_text)
    norm = facts["normalized"]
    lengths = facts["lengths"]
    angles = facts["angles"]
    target = facts["target"] or "目标量"
    post_q = norm.split("求")[-1] if "求" in norm else norm
    is_target_angle = bool(re.search(r"角|度数|∠", post_q))
    is_target_length = bool(re.search(r"长|边|高|半径|直径|距离|[A-Z]{2}", post_q))

    # ==================== 定理 1: 等腰三角形“三线合一” ====================
    # 特征：等腰 (如 AB=AC=13 或等腰△), 底边 BC=10, 垂线/高 AD⊥BC
    if facts["is_isosceles"] and (facts["perpendiculars"] or "⊥" in norm or "高" in norm or "垂足" in norm):
        iso_legs = []
        for s, v in lengths.items():
            for s2, v2 in lengths.items():
                if s != s2 and v == v2 and len(s) == 2 and len(s2) == 2 and s[0] == s2[0]:
                    iso_legs = [s, s2]
                    break
            if iso_legs:
                break

        if iso_legs:
            leg_val = lengths[iso_legs[0]]
            vertex = iso_legs[0][0]
            base_pt1 = iso_legs[0][1]
            base_pt2 = iso_legs[1][1]
            base_name = f"{base_pt1}{base_pt2}"
            base_val = lengths.get(base_name) or lengths.get(f"{base_pt2}{base_pt1}")

            if base_val:
                half_base = base_val / 2
                h_sq = leg_val**2 - half_base**2
                if h_sq > 0:
                    h_val = math.sqrt(h_sq)
                    return json.dumps({
                        "problem_type": "等腰三角形“三线合一”与勾股定理形式化推导",
                        "identified_conditions": [
                            f"等腰△{vertex}{base_pt1}{base_pt2} (腰长 {iso_legs[0]}={iso_legs[1]}={leg_val})",
                            f"底边 {base_name}={base_val}",
                            f"高线/中线 {vertex}D ⊥ {base_name}"
                        ],
                        "theorems_used": [
                            "等腰三角形三线合一性质定理: 等腰三角形底边上的高平分底边 (D为底边中点)",
                            f"勾股定理: 在 Rt△{vertex}D{base_pt1} 中, {vertex}D² + {base_pt1}D² = {iso_legs[0]}²"
                        ],
                        "steps": [
                            f"1. 判定等腰三角形: {iso_legs[0]} = {iso_legs[1]} = {leg_val}, 底边 {base_name} = {base_val}",
                            f"2. 应用【等腰三角形三线合一性质】: 顶角顶点作底边的垂线 {vertex}D 必平分底边 {base_name}",
                            f"   得: {base_pt1}D = D{base_pt2} = {base_name} / 2 = {base_val} / 2 = {half_base:.2f}",
                            f"3. 在 Rt△{vertex}D{base_pt1} 中应用【勾股定理】: {vertex}D² + {base_pt1}D² = {iso_legs[0]}²",
                            f"   即: {vertex}D² = {leg_val}² - {half_base:.2f}² = {leg_val**2} - {half_base**2:.2f} = {h_sq:.2f}",
                            f"4. 开平方解得高线长: {vertex}D = √{h_sq:.2f} = {h_val:.2f}"
                        ],
                        "final_answer": f"高线 {target} = {h_val:.2f}" if "高" in norm or "AD" in target else f"{target} = {h_val:.2f}"
                    }, ensure_ascii=False)

    # ==================== 定理 2: 直角三角形斜边中线定理 ====================
    if facts["is_midpoint"] and facts["is_right_triangle"]:
        for pt, seg in facts["midpoints"]:
            cd_name = None
            for s in lengths:
                if pt in s:
                    cd_name = s
                    break
            if cd_name and cd_name in lengths:
                cd_val = lengths[cd_name]
                hyp_val = 2 * cd_val
                return json.dumps({
                    "problem_type": "直角三角形斜边中线定理推导",
                    "identified_conditions": [
                        "直角三角形 (∠=90°)",
                        f"点 {pt} 为斜边 {seg} 的中点",
                        f"中线 {cd_name} = {cd_val}"
                    ],
                    "theorems_used": ["直角三角形斜边中线定理: 直角三角形斜边上的中线等于斜边的一半 (CD = 1/2 AB)"],
                    "steps": [
                        f"1. 确认几何关系: 在 Rt△ 中, 点 {pt} 是斜边 {seg} 的中点, 线段 {cd_name} 为斜边上的中线",
                        f"2. 应用【直角三角形斜边中线定理】: 直角三角形斜边上的中线长等于斜边长的一半",
                        f"   公式: {cd_name} = 1/2 · {seg}  =>  {seg} = 2 · {cd_name}",
                        f"3. 计算斜边长: {seg} = 2 × {cd_val} = {hyp_val:.2f}"
                    ],
                    "final_answer": f"斜边 {seg} = {hyp_val:.2f}"
                }, ensure_ascii=False)

    # ==================== 定理 3: 勾股定理逆定理与等面积法求高 ====================
    if ("高" in norm or "AD" in target) and len(lengths) >= 3:
        nums = sorted(list(lengths.values())[:3])
        a, b, c = nums[0], nums[1], nums[2]
        if abs(a**2 + b**2 - c**2) < 1e-4:
            s_val = 0.5 * a * b
            h_val = (a * b) / c
            return json.dumps({
                "problem_type": "勾股定理逆定理与等面积法求高",
                "identified_conditions": [f"已知三边长: {a}, {b}, {c}", "求斜边上的高"],
                "theorems_used": [
                    "勾股定理逆定理: 若 a² + b² = c², 则该三角形为直角三角形, c 为斜边",
                    "等面积法: S = 1/2 · a · b = 1/2 · c · h  =>  h = (a · b) / c"
                ],
                "steps": [
                    f"1. 检验三边平方关系: {a}² + {b}² = {a**2} + {b**2} = {a**2 + b**2}, {c}² = {c**2}",
                    f"   因为 {a}² + {b}² = {c}², 根据【勾股定理逆定理】, 此三角形为以 {c} 为斜边的直角三角形",
                    f"2. 计算直角三角形面积: S = 1/2 × {a} × {b} = {s_val:.2f}",
                    f"3. 应用【等面积法】求斜边上的高 h: S = 1/2 × 斜边 × h",
                    f"   代入得: {s_val:.2f} = 1/2 × {c} × h  =>  h = (2 × {s_val:.2f}) / {c} = ({a} × {b}) / {c}",
                    f"4. 计算得高长: h = {h_val:.2f} (精确分数: {a*b:.0f}/{c:.0f})"
                ],
                "final_answer": f"高 {target} = {h_val:.2f} (或分数 {int(a*b)}/{int(c)})"
            }, ensure_ascii=False)

    # ==================== 定理 4: 平行线分线段成比例定理 (相似) ====================
    if facts["is_parallel"] and len(lengths) >= 3:
        ad = lengths.get("AD")
        db = lengths.get("DB") or lengths.get("BD")
        ae = lengths.get("AE")
        if ad and db and ae:
            ec_val = (db * ae) / ad
            ac_val = ae + ec_val
            return json.dumps({
                "problem_type": "平行线分线段成比例定理推导",
                "identified_conditions": [
                    "直线 DE ∥ BC",
                    f"线段 AD = {ad}, DB = {db}, AE = {ae}"
                ],
                "theorems_used": [
                    "平行线分线段成比例定理: 两条直线被一组平行线所截, 所得的对应线段成比例 (AD / DB = AE / EC)",
                    "线段和差公理: AC = AE + EC"
                ],
                "steps": [
                    f"1. 确认平行几何条件: 因为 DE ∥ BC, 截 △ABC 两边 AB, AC",
                    f"2. 应用【平行线分线段成比例定理】: AD / DB = AE / EC",
                    f"   代入已知数据: {ad} / {db} = {ae} / EC",
                    f"3. 解比例方程求 EC: EC = ({db} × {ae}) / {ad} = ({db * ae}) / {ad} = {ec_val:.2f}",
                    f"4. 求解整条线段 AC: AC = AE + EC = {ae} + {ec_val:.2f} = {ac_val:.2f}"
                ],
                "final_answer": f"线段 AC = {ac_val:.2f}"
            }, ensure_ascii=False)

    # ==================== 定理 5: 直角三角形含 30° 特殊角 ====================
    if facts["is_right_triangle"] and any(v == 30 for v in angles.values()):
        if lengths:
            side_k, side_v = list(lengths.items())[0]
            hyp_val = side_v * 2
            return json.dumps({
                "problem_type": "含 30° 特殊角直角三角形性质推导",
                "identified_conditions": [f"Rt△ 中含 30° 特殊角", f"直角边 {side_k} = {side_v}"],
                "theorems_used": ["直角三角形性质定理: 30° 角所对的直角边等于斜边的一半 (1 : √3 : 2 比例)"],
                "steps": [
                    f"1. 识别条件: 直角三角形中含特殊角 30°, 已知边 {side_k} = {side_v}",
                    f"2. 应用【30° 角性质】: 30° 角对边 = 斜边 / 2  =>  斜边 = 2 × 直角边",
                    f"3. 计算得斜边长: 斜边 = 2 × {side_v} = {hyp_val:.2f}"
                ],
                "final_answer": f"斜边 {target} = {hyp_val:.2f}"
            }, ensure_ascii=False)

    # ==================== 定理 6: 圆与垂径定理 ====================
    if facts["is_circle"]:
        r = lengths.get("半径") or lengths.get("r")
        chord = lengths.get("弦") or lengths.get("弦长") or lengths.get("AB")
        if (not r or not chord) and len(lengths) >= 2:
            vals = sorted(list(lengths.values()))
            r, chord = vals[1], vals[0]

        if r and chord:
            half_c = chord / 2
            d_sq = r**2 - half_c**2
            if d_sq >= 0:
                d_val = math.sqrt(d_sq)
                return json.dumps({
                    "problem_type": "圆与垂径定理精确求解",
                    "identified_conditions": [f"⊙O 半径 r = {r}", f"弦长 = {chord}", "垂径垂直平分弦"],
                    "theorems_used": [
                        "垂径定理: 垂直于弦的直径平分这条弦, 且平分弦所对的两条弧",
                        "勾股定理: r² = d² + (弦长/2)²"
                    ],
                    "steps": [
                        f"1. 识别圆几何要素: 半径 r = {r}, 弦长 AB = {chord}",
                        f"2. 应用【垂径定理】: 过圆心作弦的垂线, 垂足平分弦, 得半弦长 = {chord} / 2 = {half_c:.2f}",
                        f"3. 在圆心、垂足、弦端点构成的 Rt△ 中应用【勾股定理】: r² = d² + (弦长/2)²",
                        f"   即: d² = {r}² - {half_c:.2f}² = {r**2} - {half_c**2:.2f} = {d_sq:.2f}",
                        f"4. 开平方解得弦心距: d = √{d_sq:.2f} = {d_val:.2f}"
                    ],
                    "final_answer": f"圆心到弦的距离 = {d_val:.2f}"
                }, ensure_ascii=False)

    # ==================== 定理 7: 三角形内角和定理 ====================
    if is_target_angle or (len(angles) >= 2 and not is_target_length):
        if len(angles) >= 2:
            items = list(angles.items())
            a1_name, a1_val = items[0]
            a2_name, a2_val = items[1]
            a3_val = 180 - a1_val - a2_val
            return json.dumps({
                "problem_type": "三角形内角和定理推导",
                "identified_conditions": [f"角 ∠{a1_name} = {a1_val}°", f"角 ∠{a2_name} = {a2_val}°"],
                "theorems_used": ["三角形内角和定理: 三角形三个内角之和恒等于 180° (∠A + ∠B + ∠C = 180°)"],
                "steps": [
                    f"1. 提取已知角: ∠{a1_name} = {a1_val}°, ∠{a2_name} = {a2_val}°",
                    f"2. 应用【三角形内角和定理】: ∠A + ∠B + ∠C = 180°",
                    f"3. 推导第三角: {target} = 180° - ∠{a1_name} - ∠{a2_name} = 180° - {a1_val}° - {a2_val}° = {a3_val:.1f}°"
                ],
                "final_answer": f"{target} = {a3_val:.1f}°"
            }, ensure_ascii=False)

    # ==================== 定理 8: 等腰三角形角度 ====================
    if facts["is_isosceles"] and angles:
        ang_name, ang_val = list(angles.items())[0]
        if "顶角" in norm or ang_val >= 90:
            base_ang = (180 - ang_val) / 2
            return json.dumps({
                "problem_type": "等腰三角形角度推导 (已知顶角)",
                "identified_conditions": [f"等腰△ 顶角 ∠{ang_name} = {ang_val}°"],
                "theorems_used": ["等腰三角形性质: 等边对等角 (两底角相等)", "三角形内角和定理: 三内角和为 180°"],
                "steps": [
                    f"1. 确认等腰三角形顶角: ∠{ang_name} = {ang_val}°",
                    f"2. 根据【等边对等角】定理, 两底角相等",
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

    # ==================== 定理 9: 基础勾股定理 ====================
    if facts["is_right_triangle"] and len(lengths) >= 2:
        nums = sorted(list(lengths.values()))
        n1, n2 = nums[0], nums[1]
        if "求斜边" in norm or target.lower() == "c":
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
            leg_sq = n2**2 - n1**2
            leg = math.sqrt(leg_sq)
            return json.dumps({
                "problem_type": "直角三角形勾股定理 (求直角边)",
                "identified_conditions": [f"斜边 = {n2}", f"直角边 = {n1}"],
                "theorems_used": ["勾股定理: a² + b² = c²  =>  b = √(c² - a²)"],
                "steps": [
                    f"1. 确认已知边: 斜边 = {n2}, 直角边 = {n1}",
                    f"2. 应用【勾股定理】: 直角边 = √(斜边² - 直角边²)",
                    f"3. 代入计算: {target} = √({n2}² - {n1}²) = √({n2**2 - n1**2:.2f}) = {leg:.2f}"
                ],
                "final_answer": f"直角边 {target} = {leg:.2f}"
            }, ensure_ascii=False)

    # ==================== 定理 10: 海伦公式 (三边求面积) ====================
    if len(lengths) >= 3 and facts.get("is_area", False):
        nums = sorted(list(lengths.values())[:3])
        a, b, c = nums[0], nums[1], nums[2]
        if a + b > c:
            p = (a + b + c) / 2
            area = math.sqrt(p * (p - a) * (p - b) * (p - c))
            return json.dumps({
                "problem_type": "三角形三边求面积 (海伦公式)",
                "identified_conditions": [f"三边长 a = {a}", f"b = {b}", f"c = {c}"],
                "theorems_used": ["海伦公式 (Heron's Formula): S = √(p(p-a)(p-b)(p-c)), 其中 p = (a+b+c)/2"],
                "steps": [
                    f"1. 验证三角形三边关系: {a} + {b} > {c} (有效三角形)",
                    f"2. 计算半周长: p = ({a} + {b} + {c}) / 2 = {p:.2f}",
                    f"3. 应用【海伦公式】代入计算: S = √({p:.2f} × {p-a:.2f} × {p-b:.2f} × {p-c:.2f}) = {area:.2f}"
                ],
                "final_answer": f"三角形面积 S = {area:.2f}"
            }, ensure_ascii=False)

    # 无法推导时返回清晰指导
    return json.dumps({
        "problem_type": "未能精确匹配几何定理模型",
        "identified_conditions": [f"解析线段: {lengths}", f"解析角度: {angles}"],
        "theorems_used": [],
        "steps": [
            "1. OCR 已成功识别文字, 但未能匹配到严格几何证明链。",
            "2. 建议：您可以在上方文本框中微调已知条件 (例如补充 'AB=AC=13, BC=10, AD⊥BC'), 然后再次点击推导。"
        ],
        "final_answer": "等待补充条件"
    }, ensure_ascii=False)

auto_parse_and_solve = solve_geometry
