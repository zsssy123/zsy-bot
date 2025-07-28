# zsy_model.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# 从 .env 文件中获取 HuggingFace Token
HF_API_TOKEN = os.getenv("URL_TOKEN")

# 确保 Token 存在
if HF_API_TOKEN is None:
    raise ValueError("HuggingFace API Token is missing!")

# 打印加载状态
print("🧠 正在加载 ZSYAI 模型（Mistral 7B 或其他模型）...")

# 选择更小的模型（例如 LLaMA-7B）或者 Mistral 7B，避免使用过大的模型
model_id = "mistralai/Mistral-7B-Instruct-v0.3"  # 使用公开的 Mistral-7B 或 LLaMA 7B

# 加载 tokenizer 和 model，确保使用 HuggingFace Token
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=HF_API_TOKEN)
model = AutoModelForCausalLM.from_pretrained(model_id, use_auth_token=HF_API_TOKEN, revision="int8", device_map={"cpu": 0})

# 切换到推理模式
model.eval()

print("✅ ZSYAI 模型加载完成")

# 设置最大输入 token 数量来控制内存使用
MAX_INPUT_TOKENS = 256  # 每次推理输入最多 256 个 token

def zsy_reply(messages: list[dict]) -> str:
    """
    处理用户的对话消息，并生成 ZSYAI 模型的回复。
    
    Args:
        messages: 用户和 AI 之间的对话历史列表。
    
    Returns:
        回复字符串
    """
    history = []

    # 处理每条消息
    for msg in messages:
        if msg["role"] == "user":
            query = msg["content"][:MAX_INPUT_TOKENS]  # 截断输入到最大 token 数量
            # 获取模型的回复并保留历史记录
            response, history = model.chat(tokenizer, query, history=history)
        elif msg["role"] == "assistant":
            # 如果是 AI 回复，加入历史记录
            history.append((msg["content"], ""))

    # 返回模型的最终回复
    return response
