# zsy_model.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("🧠 正在加载 ZSYAI 模型（Mistral 7B）...")

# 使用 Mistral 7B 模型并进行量化（减小内存占用）
tokenizer = AutoTokenizer.from_pretrained("mistralai/mistral-7b-instruct")  # 替换为较小的模型
model = AutoModelForCausalLM.from_pretrained("mistralai/mistral-7b-instruct", revision="int4", device_map="auto")

model.eval()
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
