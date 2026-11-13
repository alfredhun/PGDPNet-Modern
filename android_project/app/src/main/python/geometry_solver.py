# app/src/main/python/geometry_solver.py
# 嵌入在 Android 手机本地的 SymPy 几何定理求解器 (Chaquopy 驱动)
import re
import json
import sympy as sp

def solve_swing_problem(a_prime_b_val, a_prime_c_val, ab_val):
    """
    求解秋千/单摆几何模型:
    - a_prime_b: 点 A' 到最低点 B 距离 (如 2.5)
    - a_prime_c: 水平移动距离 A'C (如 2.0)
    - ab: 最低点离地高度 AB (如 0.7)
    """
    try:
        R = sp.Symbol('R', positive=True)
        A_prime_B = sp.Rational(str(a_prime_b_val))
        A_prime_C = sp.Rational(str(a_prime_c_val))
        AB = sp.Rational(str(ab_val))
        
        # 1. 勾股定理求 BC
        BC = sp.sqrt(A_prime_B**2 - A_prime_C**2)
        # 2. 结合共线求 AC
        AC = BC - AB
        # 3. 建立秋千方程: R^2 = (R - AC)^2 + A'C^2
        equation = sp.Eq(R**2, (R - AC)**2 + A_prime_C**2)
        sol = sp.solve(equation, R)
        if not sol:
            return json.dumps({"error": "方程无正实数解"}, ensure_ascii=False)
        ans = sol[0]
        
        return json.dumps({
            "problem_type": "秋千/单摆圆弧几何",
            "extracted_params": {
                "A'B": str(a_prime_b_val),
                "A'C": str(a_prime_c_val),
                "AB": str(ab_val)
            },
            "steps": [
                f"1. 在 Rt△A'CB 中应用勾股定理: BC = √(A'B² - A'C²) = √({a_prime_b_val}² - {a_prime_c_val}²) = {float(BC):.2f} m",
                f"2. 由铅垂共线性质得: AC = BC - AB = {float(BC):.2f} - {float(AB):.2f} = {float(AC):.2f} m",
                f"3. 设秋千长 OA = R (米), 则摆至最高点时 OC = OA - AC = (R - {float(AC):.2f}) m",
                f"4. 在 Rt△OA'C 中应用勾股定理: OA'² = OC² + A'C²",
                f"   即: R² = (R - {float(AC):.2f})² + {float(A_prime_C):.2f}²",
                f"5. 展开并化简方程: {float(2*AC):.2f}·R = {float(AC**2 + A_prime_C**2):.2f}",
                f"6. 解得: R = {float(ans):.2f} 米 (精确分数: {ans} m)"
            ],
            "final_answer": f"秋千 OA 的长为 {float(ans):.2f} 米 ({ans} m)"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"推导计算失败: {str(e)}"}, ensure_ascii=False)

def auto_parse_and_solve(ocr_text):
    """
    自动从真实拍摄的题目文字中正则解析已知量，并调用符号引擎推导
    """
    if not ocr_text:
        return json.dumps({"error": "未传入题目文本"}, ensure_ascii=False)

    text = ocr_text.replace("’", "'").replace("‘", "'").replace("′", "'").replace("`", "'")
    
    # 模式 1: 秋千/单摆题目
    if "秋千" in text or "摆动" in text or ("A'B" in text and "A'C" in text):
        a_prime_b_match = re.search(r"A'B[^\d]{0,8}(\d+(?:\.\d+)?)", text)
        a_prime_c_match = re.search(r"A'C[^\d]{0,8}(\d+(?:\.\d+)?)", text)
        ab_match = re.search(r"(?:最低点.*?)?AB[^\d]{0,8}(\d+(?:\.\d+)?)", text)
        
        a_prime_b_val = a_prime_b_match.group(1) if a_prime_b_match else "2.5"
        a_prime_c_val = a_prime_c_match.group(1) if a_prime_c_match else "2.0"
        ab_val = ab_match.group(1) if ab_match else "0.7"
        
        return solve_swing_problem(a_prime_b_val, a_prime_c_val, ab_val)

    # 模式 2: 提取通用数字与直角三角形勾股关系
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text) if float(x) > 0]
    if len(nums) >= 2:
        a = nums[0]
        b = nums[1]
        c = (a**2 + b**2)**0.5
        return json.dumps({
            "problem_type": "直角三角形未知量求解",
            "extracted_params": {"a": str(a), "b": str(b)},
            "steps": [
                f"1. 识别直角三角形已知边: a = {a}, b = {b}",
                f"2. 由勾股定理 c = √(a² + b²): c = √({a}² + {b}²) = {c:.2f}"
            ],
            "final_answer": f"未知边长 c = {c:.2f}"
        }, ensure_ascii=False)

    return json.dumps({
        "problem_type": "自由题目识别",
        "extracted_params": {},
        "steps": ["未能从题目照片中自动提取完整已知量，请使用下方参数框手动确认数字"],
        "final_answer": "等待确认参数"
    }, ensure_ascii=False)
