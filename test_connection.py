import sys
from openai import OpenAI
from app_config import ZHIPU_API_KEY, ZHIPU_BASE_URL, DEFAULT_VISION_MODEL

def test_api():
    print(f"正在测试智谱 API 连接...")
    print(f"Base URL: {ZHIPU_BASE_URL}")
    print(f"Model: {DEFAULT_VISION_MODEL}")
    
    client = OpenAI(
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_BASE_URL
    )
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_VISION_MODEL,
            messages=[
                {"role": "user", "content": "你好，请回复'API已正常连接'以确认通信正常。"}
            ],
            max_tokens=50
        )
        reply = response.choices[0].message.content
        print(f"API 响应成功: {reply}")
        return True
    except Exception as e:
        print(f"API 调用失败: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    test_api()
