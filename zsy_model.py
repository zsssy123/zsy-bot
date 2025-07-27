# zsy_model.py

from transformers import AutoTokenizer, AutoModel
import torch

print("🧠 正在加载 ZSYAI 模型（ChatGLM3）...")
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True).half().cuda()
model = model.eval()
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
