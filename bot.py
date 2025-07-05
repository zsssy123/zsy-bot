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

load_dotenv()

# ---🔑 Key 配置 ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")

# ---🤖 DeepSeek 接入 ---
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# ---📌 Flask 保活 ---
app = Flask('')

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>ZSY AI 欢迎页</title>
        <style>
          body {
            background: #eef1f5;
            font-family: "Segoe UI", sans-serif;
            text-align: center;
            padding-top: 80px;
          }
          h1 { font-size: 2.5em; color: #333; }
          p { font-size: 1.2em; color: #666; margin-bottom: 30px; }
          a.button {
            display: inline-block;
            margin: 10px;
            padding: 14px 28px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 1.1em;
            transition: background 0.3s;
          }
          a.button:hover { background: #218838; }
          .section {
            margin-top: 50px;
          }
        </style>
      </head>
      <body>
        <h1>👋 欢迎来到 ZSY AI</h1>
        <p>我是你的专属 AI 小搭子</p>
        <a class="button" href="/chat">进入 ZSY 聊天室</a>

        <div class="section">
          <p>👇 除了聊天，还有更多小游戏哦～</p>
          <a class="button" href="/games">🎮 查看所有小游戏</a>
        </div>
      </body>
    </html>
    """

def run_flask():
    app.run(host="0.0.0.0", port=8080)
from flask import request, jsonify, send_from_directory

@app.route("/api/chat", methods=["POST"])
def web_chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    if not user_msg:
        return jsonify({"error": "消息为空"}), 400
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个温和、真实、有点性格的 AI 伙伴。"},
                {"role": "user", "content": user_msg}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat")
def serve_chat_page():
    return send_from_directory("static", "index.html")
@app.route("/games")
def game_hub():
    return send_from_directory("static", "gamehub.html")


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
