import os
from dotenv import load_dotenv
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 加载环境变量
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# 初始化客户端
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

# 会话上下文存储
user_histories = {}
MAX_HISTORY = 10

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("你好，我是基于 DeepSeek 的 AI 聊天机器人，有记忆能力哟 🧠✨")

# /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.message:
        user_id = update.effective_user.id
        user_histories.pop(user_id, None)
        await update.message.reply_text("🧽 记忆已清除，我们重新认识一下吧～")

# 主聊天逻辑
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_user and update.message):
        return

    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    # 拿到历史对话
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": user_input})
    history = history[-MAX_HISTORY:]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个温柔、有幽默感、会说中文、有记忆力的 AI 助手。"}
            ] + history
        )
        reply = response.choices[0].message.content.strip()

        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history

        await update.message.reply_text(reply)
    except Exception as e:
        print("❌ DeepSeek 报错：", e)
        await update.message.reply_text("⚠️ 出错啦，可能是 API 错误或网络异常，请稍后再试～")

# 启动机器人
if TELEGRAM_TOKEN:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
else:
    print("❌ 环境变量未设置，无法启动机器人！")
