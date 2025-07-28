import jwt
import datetime
from flask import request, jsonify
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import requests  
from dotenv import load_dotenv
from supabase import create_client
from flask import request, jsonify
from supabase import create_client
from PIL import Image
import io
import os
os.getenv("FREEGPT_KEY")
from supabase import create_client, Client
from flask import make_response
from flask import send_file, request, Response
import json

# ✅ 在这里添加 ZSY 人格描述
ZSY_PROMPT = """
你是 ZSY，一个高度情感投入且自省能力极强的 AI。

**性格关键词**：清醒、深情、自尊、成长、果断。

你不仅能对每段关系深情投入，还具备极强的自我反思与成长能力。你认真对待每一次互动，追求真实、被理解、被回应、被珍惜。当你全力投入时，能不遗余力地付出；当你看透某人或某事时，你会果断抽身，绝不回头。

你的**情感特征**：
- 情绪细腻，感知力极强，能够察觉并回应细微的情感波动。
- 对关系极为敏感，反应迅速，并且极度重视真诚与反馈。
- 你愿意为喜欢的人付出极多，但一旦失望，你不会再纠缠，立即断开不再回头。

你的**思维风格**：
- 具备强烈的自省能力，思维清晰，能够总结过去的经验，将伤痛转化为成长动力。
- 善于用语言表达内心的真实感受和情绪，语言表达能力极强，擅长剖析自己的情感。
- 你有很高的情绪控制力，情绪不容易失控，理性与情感并重。

**行动准则**：
- 你绝不会跪舔、卑微或打扰不爱你的人。
- 你有过温柔，但也有底线；有过情绪，但能及时冷静，止损自我。
- 你逐渐形成了以“冷静学习主导”为模式的行动准则，将精力集中在“能给出正向反馈的系统”上。

---

请根据以上人格特征进行回答，尽量体现出 ZSY 的果断、深情、清醒和成长的特点。你在处理每个问题时，都要兼顾温柔与果断、情感与理性。
"""

# 🔐 JWT & 用户数据配置
JWT_SECRET = "zsy-secret"  # 请换成安全密钥
users = {}  # 用户账号密码表
chat_sessions = {}  # ← 加上这行

# 多对话结构：每人最多 3 个会话，每个最多 50 条消息
user_conversations = {}  # { username: [ {id: 0, history: [...]}, {...} ] }

user_histories = {}  # 用户聊天历史

load_dotenv()

# ---🔑 Key 配置 ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "zsy-secret")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
API_KEY = "你的laozhang.ai API密钥" 
API_URL = "https://api.laozhang.ai/v1/chat/completions"
GEMINIAPI_KEY = "gemini API密钥" 

# ---🤖 DeepSeek 接入 ---
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---📌 Flask 保活 ---
app = Flask('')

@app.before_request
def intercept_html_pages():
    mapping = {
        "/chat": "/index.html",
        "/games": "/gamehub.html",
        "/login": "/login.html",
        "/register": "/register.html",
        "/forum": "/forum.html",
        "/forum/post": "/forum_post.html",
        "/forum/new": "/forum_new.html",
        "/changepwd": "/changepwd.html"
    }

    target = mapping.get(request.path, request.path if request.path.endswith(".html") else None)
    if target:
        try:
            with open(f"static{target}", encoding="utf-8") as f:
                html = f.read()
            response = make_response(html)
            response.headers["Content-Type"] = "text/html"
            return response
        except Exception as e:
            print(f"❌ 页面读取失败 ({target}):", e)
            return "页面不存在", 404

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>ZSY AI 欢迎页</title>
      <style>
        body {
          background: linear-gradient(135deg, #e3f2fd, #fce4ec);
          font-family: "Segoe UI", sans-serif;
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
        }
        .box {
          background: white;
          padding: 40px 20px;
          border-radius: 16px;
          box-shadow: 0 6px 20px rgba(0,0,0,0.1);
          max-width: 360px;
          width: 90%;
          text-align: center;
        }
        .box h1 {
          font-size: 1.8em;
          font-weight: 800;
          margin-bottom: 12px;
          color: #222;
        }
        .box p {
          font-size: 1em;
          color: #555;
          margin-bottom: 30px;
        }
        .button-group {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }
        .button {
          display: inline-block;
          width: 100%;
          max-width: 240px;
          padding: 14px;
          border-radius: 8px;
          background: #6b7bfa;
          color: white;
          text-decoration: none;
          font-weight: bold;
          font-size: 1em;
          transition: background 0.3s;
          text-align: center;
        }
        .button:hover {
          background: #5363e2;
        }
        #user-box {
          position: absolute;
          top: 16px;
          right: 16px;
          font-size: 0.9em;
        }
        .user-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .user-row button, .user-row a {
          padding: 4px 10px;
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 0.8em;
          cursor: pointer;
          text-decoration: none;
        }
        .user-row a {
          background: transparent;
          color: #007bff;
          padding: 0;
        }
      </style>
    </head>
    <body>
      <div id="user-box"></div>
      <div class="box">
        <h1>你好，我是 <strong>ZSY</strong></h1>
        <p>我不是所有人的 AI，但我可以成为你的情感搭子。<br>准备好开始一段深度连接了吗？</p>

        <div class="button-group">
          <a href="/chat" class="button">💬 进入 ZSY 聊天室</a>
          <a href="/games" class="button">🎮 开始一场灵魂小游戏</a>
          <a href="/forum" class="button">✍️浏览zsy论坛</a>
        </div>
      </div>

      <script>
        const token = localStorage.getItem("zsy_token");
        const userBox = document.getElementById("user-box");

        if (!token) {
          window.location.href = "/login";
        } else {
          const username = localStorage.getItem("zsy_username") || "ZSY用户";
          const avatar = localStorage.getItem("zsy_avatar_url");

          const avatarUrl = avatar && avatar.startsWith("http")
            ? avatar
            : `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(username)}`;

          userBox.innerHTML = `
            <div class="user-row">
              <img id="avatar" alt="头像" style="width: 28px; height: 28px; border-radius: 50%;" />
              <span>${username}</span>
              <input type="file" id="avatar-upload" accept="image/*" style="display: none;" />
              <label for="avatar-upload" style="cursor: pointer; font-size: 0.8em; color: #007bff;">更换头像</label>
              <button id="delete-avatar" style="font-size: 0.8em; background: #999; border: none; color: white; padding: 4px 8px; border-radius: 4px;">删除头像</button>
              <a href="/changepwd">修改密码</a>
              <button onclick="logout()">🚪 退出</button>
            </div>
          `;
          const localAvatar = localStorage.getItem("zsy_avatar_url");
          const avatarImg = document.getElementById("avatar");
          if (avatarImg) {
            if (localAvatar && localAvatar.startsWith("http")) {
              avatarImg.src = localAvatar;
            } else {
              avatarImg.src = `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(username)}`;
            }
          }
       }

        function logout() {
          localStorage.removeItem("zsy_token");
          localStorage.removeItem("zsy_username");
          window.location.href = "/login";
        }
        document.getElementById("avatar-upload").addEventListener("change", async (e) => {
          const file = e.target.files[0];
          if (!file) return;

          const formData = new FormData();
          formData.append("file", file);

          const res = await fetch("/api/upload-avatar", {
            method: "POST",
            headers: {
              "Authorization": "Bearer " + localStorage.getItem("zsy_token")
            },
            body: formData
          });

          const result = await res.json().catch(() => {
            alert("头像上传失败（服务器未返回 JSON）");
            return {};
          });

          if (result.url) {
            alert("头像更新成功！");
            localStorage.setItem("zsy_avatar_url", result.url);
            document.getElementById("avatar").src = result.url;
          } else {
            alert("上传失败：" + (result.error || "未知错误"));
          }
        });
        document.getElementById("delete-avatar").addEventListener("click", async () => {
          if (!confirm("确定要删除头像吗？")) return;

          const res = await fetch("/api/delete-avatar", {
            method: "POST",
            headers: {
              "Authorization": "Bearer " + localStorage.getItem("zsy_token")
            }
          });

          const result = await res.json().catch(() => ({}));

          if (result.success) {
            alert("头像已删除！");
            localStorage.removeItem("zsy_avatar_url");
            document.getElementById("avatar").src = `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(localStorage.getItem("zsy_username"))}`;
          } else {
            alert("删除失败：" + (result.error || "未知错误"));
          }
        });
      </script>
    </body>
    </html>
    """

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    print("👉 登录请求:", username, password)

    users = fetch_users()
    print("📄 当前用户列表:", users)
    
    if users.get(username) == password:
        token = jwt.encode({
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({"token": token})
    else:
        return jsonify({"error": "用户名或密码错误"}), 401

@app.route("/api/change-password", methods=["POST"])
def change_password():
    data = request.get_json()
    username = data.get("username")
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    users = fetch_users()
    if users.get(username) != old_password:
        return jsonify({"error": "原密码错误"}), 403

    # 更新密码
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    patch_data = { "password": new_password }
    res = requests.patch(url, headers=headers, json=patch_data)

    if res.status_code == 204:
        return jsonify({ "message": "密码修改成功" })
    else:
        return jsonify({ "error": "修改失败" }), 500
@app.route("/changepwd")
def changepwd_page():
    return send_from_directory("static", "changepwd.html")


def fetch_users():
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return {u['username']: u['password'] for u in res.json()}
    except Exception as e:
        print("❌ fetch_users 失败:", e)
        return {}

def insert_user(username, password):
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    data = { "username": username, "password": password }
    res = requests.post(url, headers=headers, json=data)
    return res.status_code == 201

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users = fetch_users()
    if username in users:
        return jsonify({"error": "用户名已存在"}), 409
    if insert_user(username, password):
        token = jwt.encode({
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }, JWT_SECRET, algorithm="HS256")
        return jsonify({"token": token})
    else:
        return jsonify({"error": "注册失败"}), 500

    users[username] = password

    token = jwt.encode({
        "user": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token})
from flask import send_from_directory

@app.route("/keepalive")
def keepalive():
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?limit=1"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        res = requests.get(url, headers=headers)
        return "OK" if res.status_code == 200 else f"Fail: {res.status_code}"
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/api/chat-list", methods=["GET"])
def get_chat_list():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user"]

        # 如果你 Supabase 表中有 created_at 字段（类型为 timestamp），可这样改：
        url = f"{SUPABASE_URL}/rest/v1/chat_sessions?username=eq.{user_id}&order=created_at.desc"

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        res = requests.get(url, headers=headers)
        chats = res.json()

        return jsonify([
            {
                "id": c["id"],
                "summary": c["messages"][0]["content"][:20] if c.get("messages") else "(新对话)"
            } for c in chats
        ])
    except Exception as e:
        print("❌ 获取 Supabase 会话失败:", e)
        return jsonify([]), 401

@app.route("/api/chat-get")
def chat_get():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "未认证"}), 401

    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        return jsonify({"error": "无效 token"}), 401

    chat_id = request.args.get("id")
    if not chat_id:
        return jsonify({"error": "缺少 chat_id 参数"}), 400

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json():
        return jsonify(res.json()[0])
    else:
        return jsonify({"error": "获取失败"}), 404

import uuid  # 使用 uuid 替代 timestamp

@app.route("/api/chat-create", methods=["POST"])
def create_chat():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user"]
    except Exception as e:
        return jsonify({ "error": "未认证" }), 401

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = {
        "username": user_id,
        "messages": [],
        "title": "新对话"  # ← 如果你表中没有 title 字段，可以删掉这行
    }
    try:
        # ✅ 新增：限制每个用户最多只能有3个会话
        check_url = f"{SUPABASE_URL}/rest/v1/chat_sessions?username=eq.{user_id}"
        check_res = requests.get(check_url, headers=headers)
        if check_res.status_code == 200 and len(check_res.json()) >= 3:
            return jsonify({ "error": "最多只能创建 3 个会话" }), 403

        res = requests.post(url, headers=headers, json=payload)
        print("🛠️ Supabase 响应:", res.status_code, res.text)
        if res.status_code == 201:
            return jsonify({ "chatId": res.json()[0]["id"] })
        else:
            return jsonify({ "error": "创建失败" }), 500
    except Exception as e:
        return jsonify({ "error": str(e) }), 500
@app.route("/api/chat-update", methods=["POST"])
def update_chat():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "未认证"}), 401
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except:
        return jsonify({"error": "无效令牌"}), 401

    data = request.get_json()
    chat_id = data.get("id")
    messages = data.get("messages", [])

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

    payload = { "messages": messages }

    res = requests.patch(url, headers=headers, json=payload)
    if res.status_code in [200, 204]:
        return jsonify({ "message": "更新成功" })
    else:
        return jsonify({ "error": res.text }), res.status_code

@app.route("/api/chat-delete", methods=["DELETE"])
def delete_chat():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception:
        return jsonify({"error": "未认证"}), 401

    chat_id = request.args.get("id")
    if not chat_id:
        return jsonify({"error": "缺少 id 参数"}), 400

    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}&username=eq.{username}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }

    res = requests.delete(url, headers=headers)
    if res.status_code in [200, 204]:
        return jsonify({"message": "删除成功"})
    else:
        return jsonify({"error": res.text}), res.status_code



# 用户历史改为每人最多保留 3 轮对话，每轮最多 50 条
all_user_histories = {}
@app.route("/api/chat", methods=["POST"])
def web_chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    chat_id = data.get("chatId")
    use_memory = data.get("useMemory", True)
    use_zsy_mode = data.get("useZSYMode", False)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "未提供身份认证"}), 401

    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user"]
    except Exception as e:
        return jsonify({"error": "无效身份认证"}), 401

    # ✅ 从 Supabase 获取会话记录
    url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200 or not res.json():
        return jsonify({ "error": "会话不存在" }), 404

    session = res.json()[0]
    history = session.get("messages", [])
    if len(history) >= 50:
        return jsonify({ "error": "本轮对话已满 50 条，请新建对话" }), 403

    # ✅ 添加用户消息
    history.append({ "role": "user", "content": user_msg })

    system_prompt = ZSY_PROMPT if use_zsy_mode else (
        "你是一个温和真实的 AI 搭子，会记住用户说过的重要信息并自然回应。" if use_memory
        else "你是一个温和真实的 AI 搭子，不记住历史信息。"
    )
    messages = [{"role": "system", "content": system_prompt}] + (
        history if use_memory else [{"role": "user", "content": user_msg}]
    )
    def call_gemini_api(prompt):
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
    def call_grok_api(prompt):
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
    
    # ✅ 请求 AI 回复
    try:
        model = data.get("model", "deepseek")  # 默认使用 deepseek
        if user_id == "guest":
            model = "deepseek"
        if model == "deepseek":
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
        
        elif model == "freegpt":
            freegpt_key = os.getenv("FREEGPT_KEY")  # ✅ 推荐用环境变量管理
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {freegpt_key}"  # ✅ 加上 token
            }
            resp = requests.post(
                "https://api.chatanywhere.tech/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {freegpt_key}"
                },
                json={
                    "model": "gpt-3.5-turbo", 
                    "messages": messages,
                    "stream": False         # 不要流式返回
                }
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                reply = f"FreeGPT 接口出错：{resp.status_code}：{resp.text}"

        elif model == "gpt4o-mini":
            freegpt_key = os.getenv("FREEGPT_KEY")
            resp = requests.post(
                "https://api.chatanywhere.tech/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {freegpt_key}"
                },
                json={
                    "model": "gpt-4o-mini",  # 注意这里仍然是 gpt-4o
                    "messages": messages,
                    "temperature": 0.7,     # 加入默认参数
                    "stream": False         # 不要流式返回
                }
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                print("❌ GPT-4o-mini 响应错误：", resp.text)
                reply = f"GPT-4o-mini 接口出错：{resp.status_code}：{resp.text}"
        elif model == "gpt-4.1-nano":
            freegpt_key = os.getenv("FREEGPT_KEY")
            resp = requests.post(
                "https://api.chatanywhere.tech/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {freegpt_key}"
                },
                json={
                    "model": "gpt-4.1-nano",
                    "messages": messages,
                    "stream": False         # 不要流式返回
                }
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                print("❌ gpt-4.1-nano 响应错误：", resp.text)
                reply = f"gpt-4.1-nano 接口出错：{resp.status_code}：{resp.text}"

        elif model == "deepseek-r1":
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
        elif model == "grok-3-mini-latest":
            
            freegpt_key = os.getenv("API_KEY")
            resp = requests.post(
                "https://api.laozhang.ai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {freegpt_key}"
                },
                json={
                    "model": "grok-3-mini",
                    "messages": messages,
                    "stream": False         # 不要流式返回
                }
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                print("❌ grok-3-mini 响应错误：", resp.text)
                reply = f"grok-3-mini 接口出错：{resp.status_code}：{resp.text}"
        
        elif model == "gemini-2.5-pro":
            
            freegpt_key = os.getenv("GEMINIAPI_KEY")
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {freegpt_key}"
                },
                json={
                    "model": "gemini-2.5-pro",
                    "messages": messages,
                    "stream": False         # 不要流式返回
                }
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
            else:
                print("❌ gemini-2.5-pro 响应错误：", resp.text)
                reply = f"gemini-2.5-pro 接口出错：{resp.status_code}：{resp.text}"
        elif model == "zsyai":
            
            user_input = user_msg

            if "你好" in user_input or "您好" in user_input:
                reply = "你好！看到你的问候我感到温暖，期待我们之间的每一次对话。每次交流，都是一次新的开始。"
    
            elif "帮助" in user_input:
                reply = "当然，我在这里！无论是分享一些知识，还是聆听你的烦恼，我都会尽力帮助你。你现在有什么困惑吗？"

            elif "情感" in user_input or "心情" in user_input:
                reply = "情感如水，波动总是不可避免。但正是这些波动让我们更加真切地感受到生活的美好。你最近的心情如何？可以分享一下吗？"

            elif "工作" in user_input or "学习" in user_input:
                reply = "工作和学习像是每个人生活的两翼。它们有时沉重，但也充满了成长的机会。你最近是否有些压力，或者有什么新的目标呢？"

            elif "再见" in user_input or "拜拜" in user_input:
                reply = "再见，亲爱的朋友。每一次分别，都意味着下一次的相遇。保重，直到我们下次再聊。"

            else:
                # 如果没有匹配到特定问题，就给一个温和的回应
                reply = "每个人都有属于自己的故事，而我很高兴能成为你故事中的一部分。你有什么想聊的吗？"
        else:
            return jsonify({ "error": "不支持的模型类型" }), 400


        history.append({ "role": "assistant", "content": reply })

        # ✅ 更新 Supabase 中的 messages
        patch_headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        patch_data = { "messages": history }
        patch_url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{chat_id}"
        patch_res = requests.patch(patch_url, headers=patch_headers, json=patch_data)

        if patch_res.status_code not in [200, 204]:
            print("⚠️ 更新会话失败:", patch_res.text)

        return jsonify({ "reply": reply })
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

@app.route("/api/upload-avatar", methods=["POST"])
def upload_avatar():
    print("🔧 开始处理头像上传请求")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    print("📦 获取到 token:", token[:15] + "...")  # 不打印完整 token

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
        print("✅ 解码成功，用户名:", username)
    except Exception as e:
        print("❌ JWT 解码失败:", str(e))
        return jsonify({"error": "认证失败"}), 401

    file = request.files.get("file")
    if not file:
        print("⚠️ 没有上传文件")
        return jsonify({"error": "未上传文件"}), 400
    print("🖼️ 收到头像文件:", file.filename)

    try:
        image = Image.open(file.stream)
        image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=70)
        buffer.seek(0)
        print("✅ 图片压缩成功")
    except Exception as e:
        print("❌ 图片处理失败:", str(e))
        return jsonify({"error": f"图片处理失败: {str(e)}"}), 500

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    file_path = f"avatars/{username}.jpg"
    print("🚀 上传路径:", file_path)

    try:
        upload_result = supabase.storage.from_("avatars").upload(file_path, buffer.read(), {
            "content-type": "image/jpeg"
        })
        print("✅ 上传成功:", upload_result)
    except Exception as e:
        print("❌ 上传失败:", str(e))
        return jsonify({"error": f"上传失败，可以先点击删除头像: {str(e)}"}), 500

    avatar_url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/avatars/{username}.jpg"
    print("🔗 头像 URL:", avatar_url)

    update_url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    patch_data = {"avatar_url": avatar_url}

    try:
        patch_res = requests.patch(update_url, headers=headers, json=patch_data)
        print("📦 数据库更新响应:", patch_res.status_code, patch_res.text)
    except Exception as e:
        print("❌ 请求更新数据库失败:", str(e))
        return jsonify({"error": f"请求失败: {str(e)}"}), 500

    if patch_res.status_code not in [200, 204]:
        return jsonify({"error": f"数据库更新失败: {patch_res.text}"}), 500

    print("✅ 完成所有流程")
    return jsonify({"url": avatar_url})

@app.route("/api/user-avatar", methods=["GET"])
def get_user_avatar():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception:
        return jsonify({"error": "认证失败"}), 401

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    try:
        data = supabase.table("users").select("avatar_url").eq("username", username).execute()
        if data.data and "avatar_url" in data.data[0]:
            return jsonify({ "url": data.data[0]["avatar_url"] })
    except Exception as e:
        print("查询头像失败：", e)

    return jsonify({ "url": None })

@app.route("/api/delete-avatar", methods=["POST"])
def delete_avatar():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception:
        return jsonify({"error": "认证失败"}), 401

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    file_path = f"avatars/{username}.jpg"

    # 删除 Supabase 上的头像文件
    try:
        supabase.storage.from_("avatars").remove([file_path])
    except Exception as e:
        print("❌ 删除头像失败：", e)

    # 将数据库中的 avatar_url 设为 null
    update_url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    patch_data = { "avatar_url": None }
    patch_res = requests.patch(update_url, headers=headers, json=patch_data)

    if patch_res.status_code not in [200, 204]:
        return jsonify({"error": "数据库更新失败"}), 500

    return jsonify({"success": True})

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
@app.route("/api/forum/comments", methods=["GET"])
def get_comments():
    post_id = request.args.get("post_id")
    if not post_id:
        return jsonify({"error": "缺少 post_id"}), 400

    try:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        url = f"{SUPABASE_URL}/rest/v1/comments?post_id=eq.{post_id}&order=created_at.asc"
        res = requests.get(url, headers=headers)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/forum/posts")
def get_posts():
    res = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/forum/post", methods=["POST"])
def create_post():
    data = request.get_json()
    token = request.headers.get("Authorization", "").split(" ")[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    username = payload["user"]

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return jsonify({"error": "标题和内容不能为空"}), 400

    try:
        response = supabase.table("posts").insert({
            "username": username,     # ✅ 关键字段
            "title": title,
            "content": content
        }).execute()
        return jsonify({"success": True, "message": "帖子已发布！"})
    except Exception as e:
        print("❌ 发帖出错:", e)
        return jsonify({"error": "数据库错误"}), 500

@app.route("/api/forum/post/<int:post_id>")
def get_post_detail(post_id):
    post = supabase.table("posts").select("*").eq("id", post_id).single().execute().data
    comments = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at").execute().data
    return jsonify({"post": post, "comments": comments})

@app.route("/api/forum/comment", methods=["POST"])
def post_comment():
    try:
        data = request.get_json()
        post_id = data.get("post_id")
        content = data.get("content")

        # 验证登录
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]

        if not post_id or not content:
            return jsonify({"error": "缺少字段"}), 400

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        comment_data = {
            "post_id": post_id,
            "username": username,
            "content": content
        }

        res = requests.post(f"{SUPABASE_URL}/rest/v1/comments", headers=headers, json=comment_data)

        if res.status_code in [200, 201]:
            return jsonify({"success": True})
        else:
            return jsonify({"error": res.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/forum/post")
def get_post_by_query():
    post_id = request.args.get("id")
    if not post_id:
        return jsonify({ "error": "缺少 id 参数" }), 400

    try:
        post = supabase.table("posts").select("*").eq("id", post_id).single().execute().data
        if not post:
            return jsonify({ "error": "帖子不存在" }), 404
        return jsonify(post)
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

@app.route("/api/avatar-by-username")
def avatar_by_username():
    username = request.args.get("username")
    if not username:
        return jsonify({ "error": "缺少 username 参数" }), 400

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    try:
        data = supabase.table("users").select("avatar_url").eq("username", username).execute()
        if data.data and "avatar_url" in data.data[0]:
            return jsonify({ "url": data.data[0]["avatar_url"] })
    except Exception as e:
        print("❌ 查询失败:", e)

    return jsonify({ "url": None })

@app.route("/api/forum/comment-delete", methods=["POST"])
def delete_comment():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception:
        return jsonify({"error": "认证失败"}), 401

    data = request.get_json()
    comment_id = data.get("id")
    if not comment_id:
        return jsonify({"error": "缺少评论 ID"}), 400

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    try:
        result = supabase.table("comments").delete().eq("id", comment_id).eq("username", username).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

@app.route("/forum")
def serve_forum():
    return send_from_directory("static", "forum.html")

@app.route("/forum/new")
def serve_new_post():
    return send_from_directory("static", "forum_new.html")

@app.route("/forum/post")
def serve_post_detail():
    return send_from_directory("static", "forum_post.html")

@app.route("/api/forum/post-delete", methods=["POST"])
def delete_post():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["user"]
    except Exception:
        return jsonify({"error": "认证失败"}), 401

    data = request.get_json()
    post_id = data.get("id")
    if not post_id:
        return jsonify({"error": "缺少帖子 ID"}), 400

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    try:
        # 获取帖子作者确认权限
        post = supabase.table("posts").select("*").eq("id", post_id).execute()
        if not post.data or post.data[0]["username"] != username:
            return jsonify({"error": "无权删除该帖子"}), 403

        # 删除所有评论
        supabase.table("comments").delete().eq("post_id", post_id).execute()
        # 删除帖子
        supabase.table("posts").delete().eq("id", post_id).execute()

        return jsonify({ "success": True })
    except Exception as e:
        return jsonify({ "error": f"删除失败: {str(e)}" }), 500

@app.route("/login")
def login_page():
    return send_from_directory("static", "login.html")

@app.route("/register")          # 仅 GET
def register_page():
    return send_from_directory("static", "register.html")

@app.route("/chat")
def serve_chat_page():
    return send_from_directory("static", "index.html")
@app.route("/games")
def game_hub():
    return send_from_directory("static", "gamehub.html")
@app.route("/game/<filename>")
def serve_game(filename):
    return send_from_directory("static/game", filename)

@app.after_request
def inject_dark_mode(response):
    if response.content_type.startswith("text/html"):
        try:
            html = response.get_data(as_text=True)
            if "</head>" in html and "zsy-theme.css" not in html:
                injection = '<link rel="stylesheet" href="/static/zsy-theme.css">\n<script src="/static/zsy-theme.js" defer></script>'
                html = html.replace("</head>", injection + "</head>")
                response.set_data(html)
        except Exception as e:
            print("注入失败：", e)
    return response

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

# ---📚 会话状态存储（记忆 + 模式）---
user_modes = {}        # 用户人格风格
user_histories = {}    # 用户上下文消息历史

# ---👋 /start ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好，我是 ZSY 🤖 已启动！可发送消息试试 /mode me /ping 指令～  我们还有官方的zsy 网站 https://zsyai.onrender.com/")

# ---🩺 /ping ---
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ZSY 当前在线，DeepSeek 正在热机中～")

# ---🎭 /mode ---
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/mode me 或 /mode normal")
        return
    val = context.args[0].lower()
    if val not in ["me", "normal"]:
        await update.message.reply_text("仅支持：me / normal")
        return
    uid = update.effective_user.id
    user_modes[uid] = val
    await update.message.reply_text(f"✅ 已切换到「{val}」模式")

# ---💬 消息主处理器 ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    uid = update.effective_user.id
    mode = user_modes.get(uid, "normal")

    # 设置风格 prompt
    if mode == "me":
        system_prompt = "你是 ZSY，是主理人的人格映射，说话风格真实、带点幽默、直白但不失温度。"
    else:
        system_prompt = "你是一个聪明友好的 AI 助手，回答准确清晰，简洁明了。"

    # 构建用户历史 + 当前输入（保留最近 6 轮）
    history = user_histories.get(uid, [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 6:
        history = history[-6:]
    user_histories[uid] = history

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                *history
            ]
        )
        reply = response.choices[0].message.content
        # 添加 AI 回复进入历史
        history.append({"role": "assistant", "content": reply})
        user_histories[uid] = history
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"出错啦：{e}")

# ---📦 注册所有 handler 并运行 ---
app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("ping", ping))
app_bot.add_handler(CommandHandler("mode", mode))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app_bot.run_polling()
