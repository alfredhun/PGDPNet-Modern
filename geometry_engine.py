"""
geometry_engine.py - 平面几何图形结构化解析器
严格基于视觉可见元素，严禁幻觉臆造未标注数字
"""
import os
import json
import base64
from typing import Dict, Any
from openai import OpenAI
from app_config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEFAULT_VISION_MODEL

class GeometryEngine:
    def __init__(self, api_key: str = ZHIPU_API_KEY, base_url: str = ZHIPU_BASE_URL, model: str = DEFAULT_VISION_MODEL):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    @staticmethod
    def encode_image(img_path: str) -> str:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def _clean_json_markdown(text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def parse_diagram(self, img_path: str) -> Dict[str, Any]:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"找不到图片: {img_path}")

        b64_img = self.encode_image(img_path)
        ext = os.path.splitext(img_path)[1].lower().replace(".", "")
        mime = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"

        # 严格防幻觉、严格保真 Prompt
        system_prompt = """你是一个高精度的平面几何图形解析器。
你的唯一原则是：【严格基于视觉实际可见内容输出，绝对禁止臆造、推测任何未在图上标注的数值、字母或关系】。

请提取以下要素：
1. points: 图中实际标出的点名（例如 ["O", "C", "A", "B", "A'"]，带撇号的点如 A' 必须真实反映）。
2. lines: 实线与虚线段。标明线型（solid 或 dashed）。
3. collinear: 共线点组合（例如 O, C, A, B 在同一直线/竖直线上）。
4. visual_symbols:
   - right_angles: 图中实际画有小方块（直角标记）的位置及两臂（例如直角符号在点 C 处，臂为 A'C 与 OC/OB；若点 A 处只有短横线/刻度而非直角小方块，请准确区分）。
   - parallel_arrows: 图中实际画有平行箭头标记的线段（无则为空列表 []）。
   - equal_marks: 图中实际画有相等单/双刻度线的线段（无则为空列表 []）。
   - explicit_values: 图中实际印有数字的标注（例如 "60°"、"5cm"），若没有印任何数字，必须返回 []。
5. diagram_logic_forms: 基于图中实际点和标记生成的标准几何形式化谓词：
   - 垂直: "Perpendicular(Line(A', C), Line(O, B))"
   - 共线: "PointLiesOnLine(C, Line(O, B))", "PointLiesOnLine(A, Line(O, B))"
   - 旋转/全等隐式对应（根据 A' 是 A 的对应点）: 如 "Equals(LengthOf(Line(O, A')), LengthOf(Line(O, A)))", "Equals(LengthOf(Line(A', B)), LengthOf(Line(A, B)))" 等。

输出必须是标准的合法 JSON，格式如下：
{
  "points": ["O", "C", "A", "B", "A'"],
  "collinear_groups": [
    ["O", "C", "A", "B"]
  ],
  "lines": [
    {"endpoints": ["O", "B"], "style": "solid_and_dashed"},
    {"endpoints": ["O", "A'"], "style": "dashed"},
    {"endpoints": ["A'", "C"], "style": "dashed"},
    {"endpoints": ["A'", "A"], "style": "dashed"},
    {"endpoints": ["A'", "B"], "style": "dashed"}
  ],
  "visual_symbols": {
    "right_angles": [
      {"vertex": "C", "arms": ["A'C", "OB"]}
    ],
    "parallel_arrows": [],
    "equal_marks": [],
    "explicit_values": []
  },
  "diagram_logic_forms": [
    "PointLiesOnLine(C, Line(O, B))",
    "PointLiesOnLine(A, Line(O, B))",
    "Perpendicular(Line(A', C), Line(O, B))"
  ]
}
只输出 JSON，严禁添加任何多余文字。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请对该几何图片进行严格的视觉要素与几何拓扑提取，切勿捏造未标注的数字。"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}}
                    ]
                }
            ],
            temperature=0.0
        )

        raw = response.choices[0].message.content
        cleaned = self._clean_json_markdown(raw)
        try:
            return json.loads(cleaned)
        except Exception:
            return {"raw_response": raw}

if __name__ == "__main__":
    import sys
    engine = GeometryEngine()
    target_img = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793952677457_0c779dfd.png"
    result = engine.parse_diagram(target_img)
    print(json.dumps(result, ensure_ascii=False, indent=2))
