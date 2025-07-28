from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 从 .env 文件中获取 HuggingFace Token
HF_API_TOKEN = os.getenv("URL_TOKEN")

# 确保 Token 存在
if HF_API_TOKEN is None:
    raise ValueError("HuggingFace API Token is missing!")

print("🧠 正在加载 ZSYAI 模型（Mistral 7B）...")

# 加载 Mistral 7B 模型和 tokenizer
model_id = "mistralai/Mistral-7B-Instruct-v0.3"  # 使用正确的模型 ID
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=HF_API_TOKEN)
model = AutoModelForCausalLM.from_pretrained(model_id, use_auth_token=HF_API_TOKEN)

model.eval()  # 只用推理模式
print("✅ ZSYAI 模型加载完成")

def zsy_reply(messages: list[dict]) -> str:
    history = []
    for msg in messages:
        if msg["role"] == "user":
            query = msg["content"]
            response, history = model.chat(tokenizer, query, history=history)
        elif msg["role"] == "assistant":
            history.append((msg["content"], ""))
    return response

