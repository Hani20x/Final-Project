import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

TOKEN = "7698768664:AAE9WDT2_duyrFLcICLZB2OE_06zQdbCpI0"
DATA_FILE = "tasks.json"

# States for conversation
ADDING_TASK, DELETING_TASK = range(2)

# Load tasks from file
def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save tasks to file
def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)

# Load tasks at startup
user_tasks = load_tasks()

def get_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("/add"), KeyboardButton("/list")],
        [KeyboardButton("/delete"), KeyboardButton("/help")]
    ], resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Hello! I'm your To-Do bot.\n"
        "Use the buttons below to manage your tasks:",
        reply_markup=get_keyboard()
    )
    return ConversationHandler.END

def add_task(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📝 Please send me the task you want to add:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
    )
    return ADDING_TASK

def adding_task(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    task = update.message.text
    
    if task.lower() == "cancel":
        update.message.reply_text("❌ Task addition canceled.", reply_markup=get_keyboard())
        return ConversationHandler.END
    
    if user_id not in user_tasks:
        user_tasks[user_id] = []
    user_tasks[user_id].append(task)
    save_tasks(user_tasks)
    update.message.reply_text(f"✅ Task added: {task}", reply_markup=get_keyboard())
    return ConversationHandler.END

def list_tasks(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        update.message.reply_text("🗒️ Your task list is empty.", reply_markup=get_keyboard())
        return ConversationHandler.END

    message = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
    update.message.reply_text("📝 Your Tasks:\n" + message, reply_markup=get_keyboard())
    return ConversationHandler.END

def delete_task(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    tasks = user_tasks.get(user_id, [])
    
    if not tasks:
        update.message.reply_text("🗒️ Your task list is empty.", reply_markup=get_keyboard())
        return ConversationHandler.END
    
    message = "📝 Your Tasks:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
    update.message.reply_text(
        f"{message}\n\nPlease send the number of the task to delete:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
    )
    return DELETING_TASK

def deleting_task(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    tasks = user_tasks.get(user_id, [])
    text = update.message.text
    
    if text.lower() == "cancel":
        update.message.reply_text("❌ Task deletion canceled.", reply_markup=get_keyboard())
        return ConversationHandler.END
    
    if not text.isdigit():
        update.message.reply_text("⚠️ Please send only the task number.", reply_markup=get_keyboard())
        return DELETING_TASK
    
    index = int(text) - 1
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        save_tasks(user_tasks)
        update.message.reply_text(f"🗑️ Removed task: {removed}", reply_markup=get_keyboard())
    else:
        update.message.reply_text("❌ Invalid task number. Please try again.", reply_markup=get_keyboard())
        return DELETING_TASK
    
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "ℹ️ How to use this bot:\n"
        "- Click /add then send your task\n"
        "- Click /list to see all tasks\n"
        "- Click /delete then send task number",
        reply_markup=get_keyboard()
    )
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Operation canceled.", reply_markup=get_keyboard())
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('add', add_task),
            CommandHandler('delete', delete_task)
        ],
        states={
            ADDING_TASK: [MessageHandler(Filters.text & ~Filters.command, adding_task)],
            DELETING_TASK: [MessageHandler(Filters.text & ~Filters.command, deleting_task)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("list", list_tasks))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, help_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()