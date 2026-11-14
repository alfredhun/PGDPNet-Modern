# test_geometry_solver.py
# 自动化测试高精度几何定理推导引擎
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "android_project", "app", "src", "main", "python"))
from geometry_solver import solve_geometry

test_cases = [
    # 1. 等腰三角形三线合一（极其经典的难题，此前曾被粗糙勾股算错）
    ("18.(8分)如图,在△ABC中,点D在BC上,AB=AC=13,BC=10,AD⊥BC,垂足为D.求AD的长.", "等腰三角形“三线合一”", "12.00"),
    # 2. 勾股逆定理与等面积法求斜边上的高
    ("如图，在△ABC中，AB=5，AC=12，BC=13，求BC边上的高AD。", "等面积法", "4.62"),
    # 3. 直角三角形斜边中线定理
    ("在Rt△ABC中，∠C=90°，点D是AB的中点，CD=4，求AB的长。", "斜边中线定理", "8.00"),
    # 4. 平行线分线段成比例定理
    ("如图，DE∥BC，AD=2，DB=3，AE=4，求AC的长。", "平行线分线段成比例", "10.00"),
    # 5. 含 30° 特殊角直角三角形
    ("如图，在Rt△ABC中，∠C=90°，∠A=30°，BC=4，求斜边AB的长。", "30°", "8.00"),
    # 6. 直角三角形基础勾股定理
    ("在Rt△ABC中，∠C=90°，AB=13，AC=5，求BC的长。", "勾股定理", "12.00"),
    # 7. 三角形内角和定理
    ("已知△ABC中，∠A=50°，∠B=70°，求∠C的度数。", "内角和定理", "60.0°"),
    # 8. 等腰三角形角度推导
    ("等腰△ABC中，顶角∠A=40°，求底角∠B的度数。", "等腰三角形", "70.0°"),
    # 9. 圆与垂径定理
    ("在⊙O中，半径r=5，弦长AB=8，求圆心O到弦AB的距离。", "垂径定理", "3.00")
]

print("Running High-Accuracy Geometry Theorem Prover Test Suite...")
for text, expected_kw, expected_ans in test_cases:
    res_str = solve_geometry(text)
    res = json.loads(res_str)
    print(f"✓ [测试题]: {text}")
    print(f"  题型: {res['problem_type']}")
    print(f"  答案: {res['final_answer']}")
    assert (expected_kw in res['problem_type'] or 
            expected_kw in " ".join(res['theorems_used']) or 
            "InterGPS" in res['problem_type']), f"Keyword '{expected_kw}' not in result: {res}"
    assert expected_ans in res['final_answer'], f"Expected '{expected_ans}' in '{res['final_answer']}'"

print("\n🎉 全部 9 项高精度几何定理推导测试全部通过！")

# 额外测试：原生 InterGPS 17 项几何定理库底层接口
print("\nVerifying Native InterGPS 17 Theorems Interface...")
from intergps import ExtendedDefinition, LogicParser, LogicSolver
logic = ExtendedDefinition(debug=False)
parser = LogicParser(logic)
parser.logic.define_point(['A', 'B', 'C'])
parser.logic.define_line('A', 'B')
parser.logic.define_line('B', 'C')
parser.logic.define_line('A', 'C')
parser.dfsParseTree(parser.parse('Equals(LengthOf(Line(A, B)), 6)'))
parser.dfsParseTree(parser.parse('Equals(LengthOf(Line(B, C)), 8)'))
parser.dfsParseTree(parser.parse('Equals(MeasureOf(Angle(A, B, C)), 90)'))
target = parser.findTarget(parser.parse('Find(LengthOf(Line(A, C)))'))
solver = LogicSolver(parser.logic)
solver.initSearch()
ans, steps, step_lst = solver.Search(target=target, order_list=None, round_or_step=False, upper_bound=20, enable_low_first=False)
assert ans == 10.0, f"Expected 10.0, got {ans}"
print(f"✓ InterGPS Core 17-Theorems Engine Test Passed: 6-8-10 Right Triangle => AC = {ans} (steps: {steps})")

