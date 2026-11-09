import os
import json
import base64
from openai import OpenAI
from app_config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEFAULT_VISION_MODEL

def encode_image(img_path: str) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def parse_geometry_diagram(img_path: str):
    client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)
    b64_img = encode_image(img_path)
    
    # 严格按照 PGDP / Inter-GPS 体系的标准几何谓词定义 Prompt
    system_prompt = """你是一个高精度的平面几何图形解析器（遵照 PGDPNet 与 Inter-GPS 标准规范）。
请分析图片中的平面几何图形，提取图元、视觉标注符号及几何拓扑关系。

请输出合法的 JSON 格式，字段规范如下：
{
  "points": ["A", "B", "C", ...],
  "lines": ["AB", "BC", "CD", ...],
  "circles": ["Circle(O)"],
  "symbols": {
    "right_angles": [
      {"vertex": "B", "arms": ["AB", "BC"]}
    ],
    "parallel_arrows": [
      {"line1": "AB", "line2": "CD"}
    ],
    "equal_marks": [
      {"seg1": "AB", "seg2": "CD"}
    ],
    "angles_with_values": [
      {"angle": "Angle(A, B, C)", "degree": 60}
    ],
    "lengths_with_values": [
      {"line": "Line(A, B)", "length": 5}
    ]
  },
  "diagram_logic_forms": [
    "Perpendicular(Line(A, B), Line(B, C))",
    "Parallel(Line(A, B), Line(C, D))",
    "PointLiesOnLine(D, Line(B, C))",
    "Equals(LengthOf(Line(A, B)), LengthOf(Line(A, C)))",
    "MeasureOf(Angle(A, B, C)) = 60"
  ]
}
注意：只输出合法 JSON，不要有任何多余的 Markdown 标记或客套话。"""

    print(f"正在对图片 {img_path} 进行多模态几何拓扑解析...")
    response = client.chat.completions.create(
        model=DEFAULT_VISION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请提取该几何图的所有图元、标注与 diagram_logic_forms。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                ]
            }
        ],
        temperature=0.1
    )
    
    raw = response.choices[0].message.content.strip()
    # 清理 markdown codeblock
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    
    try:
        parsed = json.loads(raw)
        return parsed
    except Exception as e:
        print(f"JSON 解析失败: {e}\n原始返回:\n{raw}")
        return {"raw": raw}

if __name__ == "__main__":
    demo_img = r"f:\测试\PGDP\demo\demo_images\106.png"
    result = parse_geometry_diagram(demo_img)
    print("\n======== 几何解析结果 ========")
    print(json.dumps(result, ensure_ascii=False, indent=2))
