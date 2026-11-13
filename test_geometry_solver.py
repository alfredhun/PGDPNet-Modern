# test_geometry_solver.py
# 自动化测试形式化几何定理求解器
import sys
import os
import json

# 加入 android_project 中的 solver 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "android_project", "app", "src", "main", "python"))

from geometry_solver import solve_geometry

test_cases = [
    ("在Rt△ABC中，∠C=90°，AB=13，AC=5，求BC的长", "直角三角形勾股定理 (求直角边)", "12.00"),
    ("已知△ABC中，∠A=50°，∠B=70°，求∠C的度数", "三角形内角和定理角度推导", "60.0°"),
    ("等腰△ABC中，顶角∠A=40°，求底角∠B的度数", "等腰三角形角度推导 (已知顶角)", "70.0°"),
    ("已知等边三角形边长为6，求其面积", "等边三角形几何计算", "15.59"),
    ("如图，已知直线AB∥CD，∠1=55°，求∠2的同旁内角", "平行线性质定理推导", "125.0°"),
    ("在⊙O中，半径r=5，弦长AB=8，求圆心O到弦AB的距离", "圆与垂径定理计算", "3.00"),
    ("已知△ABC三边长分别为a=3, b=4, c=5，求△ABC的面积", "三角形三边求面积 (海伦公式)", "6.00"),
    ("已知Rt△ABC中，∠C=90°，∠A=30°，BC=4，求斜边AB的长", "含30°特殊角直角三角形性质", "8.00")
]

print("Running General Geometry Solver Verification Suite...")
for text, expected_type, expected_ans in test_cases:
    res_str = solve_geometry(text)
    res = json.loads(res_str)
    print(f"✓ [测试题]: {text}")
    print(f"  题型: {res['problem_type']}")
    print(f"  答案: {res['final_answer']}")
    assert expected_ans in res['final_answer'], f"Expected {expected_ans} in {res['final_answer']}"

print("\n🎉 全部通用几何求解测试用例均验证通过！")
