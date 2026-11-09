"""
fusion_pipeline.py - 端到端几何试题综合解析流水线
处理混合试题：题干文字 OCR + 数学公式 LaTeX 化 + 几何拓扑逻辑融合
"""
import os
import json
import base64
from typing import Dict, Any
from openai import OpenAI
from app_config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEFAULT_VISION_MODEL

class QuestionFusionPipeline:
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

    def process_full_question(self, img_path: str) -> Dict[str, Any]:
        """
        处理整张几何试题截图（题干 + 图形），输出融合后的全套结构化数据
        """
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"文件不存在: {img_path}")

        b64_img = self.encode_image(img_path)
        ext = os.path.splitext(img_path)[1].lower().replace(".", "")
        mime = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"

        system_prompt = """你是一个专业的初高中数学几何题目全要素解析系统。
请仔细分析用户上传的数学试题图片（包含题干文字、数学公式以及几何图形），完成以下任务：

1. 【question_text】：完整转录题干。
   - 所有数学公式、变量、角、线段、度数、方程一律使用标准 LaTeX 格式（行内用 $...$，行间用 $$...$$）。
   - 保留原题段落格式与选项/设问结构。

2. 【geometry_parsing】：按照 PGDP (Plane Geometry Diagram Parsing) 标准解析配图：
   - points: 图中出现的几何点（大写英文字母列表）
   - lines: 主要线段/直线列表
   - circles: 圆（如 ["Circle(O)"]）
   - visual_marks: 图中显式标注的符号（直角标记、平行箭头、相等线段刻度标记）

3. 【unified_logic_forms】：将【题干中给出的几何条件】与【图中解析出的拓扑关系】做逻辑融合与对齐，输出统一的形式化逻辑谓词列表（Inter-GPS/PGDP 标准规范）：
   - 包含示例：
     "PointLiesOnLine(D, Line(B, C))"
     "Perpendicular(Line(A, B), Line(B, C))"
     "Parallel(Line(A, B), Line(C, D))"
     "MeasureOf(Angle(A, B, C)) = 90"
     "Equals(LengthOf(Line(A, B)), LengthOf(Line(A, C)))"
     "Equals(LengthOf(Line(B, D)), LengthOf(Line(D, C)))" (中点条件)

请输出严格的 JSON 字符串，字段结构如下：
{
  "question_text": "...",
  "geometry_parsing": {
    "points": [...],
    "lines": [...],
    "circles": [...],
    "visual_marks": {
      "right_angles": [...],
      "parallel_arrows": [...],
      "equal_marks": [...]
    }
  },
  "unified_logic_forms": [
    "...",
    "..."
  ]
}
只输出合法 JSON，不添加多余说明。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请解析该试题的文字公式与几何拓扑逻辑。"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}}
                    ]
                }
            ],
            temperature=0.1
        )

        raw = response.choices[0].message.content
        cleaned = self._clean_json_markdown(raw)
        try:
            return json.loads(cleaned)
        except Exception:
            return {"raw_response": raw}

if __name__ == "__main__":
    pipeline = QuestionFusionPipeline()
    # 支持直接传入任意题图
    print("QuestionFusionPipeline 初始化完成，随时可传入图片处理。")
