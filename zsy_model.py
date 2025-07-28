# zsy_model.py
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("🧠 正在加载 ZSYAI 模型（Mistral 7B）...")

HF_API_TOKEN =os.getenv("URL_TOKEN")
# 使用量化后的 Mistral-7B（int4 版本）
model = AutoModelForCausalLM.from_pretrained("mistralai/mistral-7b-instruct", revision="int4", device_map="auto",use_auth_token=HF_API_TOKEN)
tokenizer = AutoTokenizer.from_pretrained("mistralai/mistral-7b-instruct", use_auth_token=HF_API_TOKEN)

model.eval()  # 只用推理模式
print("✅ ZSYAI 模型加载完成")

def zsy_reply(messages: list[dict]) -> str:
    history = []
    for msg in messages:
        if msg["role"] == "user":
            query = msg["content"]
            response, history = model.chat(tokenizer, query, history=history)
        elif msg["role"] == "assistant":
            # 保留历史上下文
            history.append((msg["content"], ""))
    return response
