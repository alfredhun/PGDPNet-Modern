# app/src/main/python/geometry_solver.py
# 嵌入在 Android 手机本地的 SymPy 几何定理求解器 (Chaquopy 驱动)
import sympy as sp
import json

def solve_swing_problem(a_prime_b_val, a_prime_c_val, ab_val):
    """
    求解秋千/单摆几何模型:
    - a_prime_b: 点 A' 到最低点 B 距离 (如 2.5)
    - a_prime_c: 水平移动距离 A'C (如 2.0)
    - ab: 最低点离地高度 AB (如 0.7)
    """
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
    ans = sol[0]
    
    return json.dumps({
        "steps": [
            f"1. 在 Rt△A'CB 中: BC = √(A'B² - A'C²) = {float(BC):.2f} m",
            f"2. 由共线点性质: AC = BC - AB = {float(BC):.2f} - {float(AB):.2f} = {float(AC):.2f} m",
            f"3. 设秋千长 OA=R, 则 OC = R - {float(AC):.2f} m",
            f"4. 在 Rt△OA'C 中列方程: R² = (R - {float(AC):.2f})² + {float(A_prime_C):.2f}²",
            f"5. 解得: R = {float(ans):.2f} 米 ({ans} m)"
        ],
        "final_answer": f"{float(ans):.2f} 米"
    }, ensure_ascii=False)

def solve_pythagorean(a, b=None, c=None):
    """通用直角三角形边长求解器"""
    if c is None and a and b:
        # 求斜边
        hyp = sp.sqrt(sp.Rational(str(a))**2 + sp.Rational(str(b))**2)
        return json.dumps({"answer": f"{float(hyp):.2f}", "step": f"c = √({a}² + {b}²) = {float(hyp):.2f}"})
    elif b is None and a and c:
        # 求直角边
        leg = sp.sqrt(sp.Rational(str(c))**2 - sp.Rational(str(a))**2)
        return json.dumps({"answer": f"{float(leg):.2f}", "step": f"b = √({c}² - {a}²) = {float(leg):.2f}"})
    return json.dumps({"error": "参数不足"})
