async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        print("⚠️ /start 被触发但没有 message")
        return
    await update.message.reply_text("你好，我是基于 DeepSeek 的 AI 聊天机器人，有记忆能力哟 🧠✨")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_user and update.message):
        print("⚠️ /clear 时无法获取用户信息")
        return
    user_id = update.effective_user.id
    user_histories.pop(user_id, None)
    await update.message.reply_text("🧽 记忆已清除，我们重新认识一下吧～")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message and update.message.text and update.effective_user):
        print("⚠️ chat() 收到无效消息结构")
        return

    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    ...
