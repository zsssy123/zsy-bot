import os
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# 💡 DeepSeek 配置
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🧠 用户模式字典（用于切换人格风格）
user_modes = {}

# 🚀 Flask 保活
app = Flask('')

@app.route('/')
def home():
    return "✅ ZSY bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# 🎯 /start 指令处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好，我是 ZSY 🤖 已上线！你可以发送消息或试试 /mode me /ping 等指令")

# ⏱️ /ping 指令
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ZSY 当前在线，一切正常 ✅")

# 🧬 /mode 指令切换人格
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("用法：/mode normal 或 /mode me")
        return
    mode = context.args[0].lower()
    if mode not in ["normal", "me"]:
        await update.message.reply_text("只支持模式：normal 或 me 😅")
        return
    user_modes[update.effective_user.id] = mode
    await update.message.reply_text(f"✅ 已切换为「{mode}」模式")

# 💬 主消息处理器
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    uid = update.effective_user.id
    mode = user_modes.get(uid, "normal")

    try:
        if mode == "me":
            prompt = "你是 ZSY，是主理人的镜像人格，说话风格像他本人，真实、带点幽默、不喜欢敷衍。"
        else:
            prompt = "你是一个帮助用户的 AI 助手，说话简洁清晰。"

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"💥 出错啦：{e}")

# 🧩 构建并添加所有 handler
app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("ping", ping))
app_bot.add_handler(CommandHandler("mode", mode))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app_bot.run_polling()
