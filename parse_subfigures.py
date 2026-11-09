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

def parse_multi_subfigures(img_path: str):
    b64_img = encode_image(img_path)
    
    prompt = """请对这张包含多个子图（图 1、图 2、图 3）的平面直角坐标系几何探究题进行极其细致的结构化提取。
分别针对每个子图（图 1、图 2、图 3）提取：
1. 坐标系信息：x轴、y轴、原点 O
2. 图中顶点标识（Points）：如 A, B, C, D, E, O, P, Q 等
3. 出现的线段与多边形（Lines / Triangles）
4. 点与线段的位置拓扑关系（Collinear 共线、交点 Intersection、在坐标轴上等）
5. 形式化几何谓词表达（diagram_logic_forms，采用标准 Inter-GPS / PGDP 形式，如 PointLiesOnLine, IntersectionPoint, Perpendicular 等）
6. 子图间的异同/演变关系（如辅助线的添加、图形的平移/旋转/对称）

输出严格合法的 JSON 格式。"""

    response = client.chat.completions.create(
        model=DEFAULT_VISION_MODEL,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
            ]}
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
    return json.loads(raw.strip())

if __name__ == "__main__":
    img_path = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1794185161439_b745d713.png"
    try:
        res = parse_multi_subfigures(img_path)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        with open("f:/测试/subfigures_parsed.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error: {e}")
