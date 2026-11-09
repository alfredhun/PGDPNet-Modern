import os

# 智谱 API 配置 (优先读取环境变量，避免硬编码上传泄露)
ZHIPU_API_KEY = os.environ.get("ZHIPUAI_API_KEY", "")
ZHIPU_BASE_URL = os.environ.get("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

# 默认视觉模型 (支持 glm-4v-flash, glm-4v, glm-4v-plus)
DEFAULT_VISION_MODEL = "glm-4v-flash"
