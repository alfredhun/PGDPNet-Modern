"""
test_two_diagrams.py - 测试解析用户上传的两张新图
图 1: 多子图 (图1, 图2, 图3) 坐标几何探究
图 2: 一次函数 / 行程分段折线坐标图
"""
import os
import sys
import json
import base64
from openai import OpenAI
from app_config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEFAULT_VISION_MODEL

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)

def encode_image(img_path: str) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def parse_advanced_diagram(img_path: str, diagram_desc: str):
    print("=" * 65)
    print(f"[*] 正在解析: {diagram_desc}")
    print(f"[*] 图像路径: {img_path}")
    print("=" * 65)
    
    b64_img = encode_image(img_path)
    
    system_prompt = """你是一个全功能的数学图形与坐标系结构化解析系统。
请仔细分析输入的数学图，若包含多个子图（如 图1、图2、图3），请分别对每个子图结构化输出；若为函数坐标系图，请提取坐标轴、分段点与数值投影。

请严格输出合法 JSON 格式：
1. 若为【多子图几何题】：
{
  "diagram_type": "multi_subfigures_coordinate_geometry",
  "subfigures": [
    {
      "sub_id": "图 1",
      "coordinate_system": {"axes": ["x", "y"], "origin": "O"},
      "points": ["A", "B", "C", "D", "E", "O"],
      "collinear": [
        ["A", "O", "C"],
        ["B", "E", "O"],
        ["B", "D", "C"],
        ["A", "E", "D"]
      ],
      "diagram_logic_forms": [
        "PointLiesOnLine(O, Line(A, C))",
        "PointLiesOnLine(E, Line(B, O))",
        "PointLiesOnLine(D, Line(B, C))",
        "IntersectionPoint(E, Line(A, D), Line(B, O))"
      ]
    },
    ...
  ]
}

2. 若为【函数坐标系 / 分段折线图】：
{
  "diagram_type": "function_cartesian_graph",
  "axes": {
    "x_axis": {"label": "x/h", "variable": "x", "unit": "h"},
    "y_axis": {"label": "y/km", "variable": "y", "unit": "km"},
    "origin": "O"
  },
  "critical_points": [
    {"name": "O", "x_val": 0, "y_val": 0},
    {"name": "A", "x_val": "投影点", "y_val": "a"},
    {"name": "B", "x_val": "投影点", "y_val": "a"},
    {"name": "C", "x_val": 4, "y_val": 480},
    {"name": "G", "x_val": "F", "y_val": 480},
    {"name": "E", "x_val": "E", "y_val": 0}
  ],
  "segments_and_polylines": [
    {"polyline": "O-C-E", "type": "broken_line"},
    {"polyline": "O-A-B-G", "type": "piecewise_with_horizontal_pause"}
  ],
  "axis_ticks_and_labels": {
    "x_ticks": ["O", "1", "4", "E", "F"],
    "y_ticks": ["O", "a", "480"]
  },
  "semantic_properties": [
    "HorizontalSegment(A, B) -> y is constant (pause/stay)",
    "PeakPoint(C) -> max y is 480 at x=4"
  ]
}

只输出纯 JSON，不添加多余解释。"""

    response = client.chat.completions.create(
        model=DEFAULT_VISION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请结构化解析这张数学图的所有几何/函数要素与拓扑关系。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    
    try:
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e), "raw": raw}

if __name__ == "__main__":
    img1 = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793957597905_692229e0.png"
    img2 = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793957771927_2f5029c4.png"
    
    res1 = parse_advanced_diagram(img1, "【图像 1】多子图坐标几何综合题 (图1, 图2, 图3)")
    print(json.dumps(res1, ensure_ascii=False, indent=2))
    
    res2 = parse_advanced_diagram(img2, "【图像 2】一次函数/分段折线行程图")
    print(json.dumps(res2, ensure_ascii=False, indent=2))
    
    # 保存结果
    with open("f:/测试/res_img1_multisub.json", "w", encoding="utf-8") as f:
        json.dump(res1, f, ensure_ascii=False, indent=2)
    with open("f:/测试/res_img2_function.json", "w", encoding="utf-8") as f:
        json.dump(res2, f, ensure_ascii=False, indent=2)
    print("\n[OK] 两次解析结果已分别保存至 res_img1_multisub.json 和 res_img2_function.json")
