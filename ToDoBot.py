import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

# Token and data file constants
TOKEN = "7698768664:AAE9WDT2_duyrFLcICLZB2OE_06zQdbCpI0"
DATA_FILE = "tasks.json"

# States for conversation
ADDING_TASK, DELETING_TASK = range(2)

class TodoBot:
    """
    A Telegram bot to manage user to-do lists.
    """

    def __init__(self):
        """
        Initializes the TodoBot and loads tasks from the data file.
        """
        self.user_tasks = self._load_tasks()

    def _load_tasks(self):
        """
        Loads tasks from the JSON data file.

        Returns:
            dict: A dictionary where keys are user IDs and values are lists of tasks.
        """
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}

    def _save_tasks(self):
        """
        Saves the current user tasks to the JSON data file.
        """
        with open(DATA_FILE, "w") as f:
            json.dump(self.user_tasks, f)

    def _get_keyboard(self):
        """
        Returns the standard reply keyboard for the bot.

        Returns:
            ReplyKeyboardMarkup: The keyboard layout.
        """
        return ReplyKeyboardMarkup([
            [KeyboardButton("/add"), KeyboardButton("/list")],
            [KeyboardButton("/delete"), KeyboardButton("/help")]
        ], resize_keyboard=True)

    def _reply_with_keyboard(self, update: Update, message: str, cancel_button: bool = False):
        """
        Sends a reply message with the appropriate keyboard.

        Args:
            update (Update): The update object from Telegram.
            message (str): The message to send.
            cancel_button (bool): If True, shows a "Cancel" button.
        """
        if cancel_button:
            keyboard = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
        else:
            keyboard = self._get_keyboard()
        update.message.reply_text(message, reply_markup=keyboard)

    def start(self, update: Update, context: CallbackContext):
        """
        Handles the /start command, greeting the user and providing the main keyboard.
        """
        self._reply_with_keyboard(
            update,
            "👋 Hello! I'm your To-Do bot.\nUse the buttons below to manage your tasks:"
        )
        return ConversationHandler.END

    def add_task(self, update: Update, context: CallbackContext):
        """
        Initiates the task addition conversation, asking the user for the task.
        """
        self._reply_with_keyboard(update, "📝 Please send me the task you want to add:", cancel_button=True)
        return ADDING_TASK

    def adding_task(self, update: Update, context: CallbackContext):
        """
        Receives the task from the user and adds it to their list.
        """
        user_id = str(update.effective_user.id)
        task = update.message.text

        if task.lower() == "cancel":
            self._reply_with_keyboard(update, "❌ Task addition canceled.")
            return ConversationHandler.END

        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task)
        self._save_tasks()
        self._reply_with_keyboard(update, f"✅ Task added: {task}")
        return ConversationHandler.END

    def list_tasks(self, update: Update, context: CallbackContext):
        """
        Lists all tasks for the current user.
        """
        user_id = str(update.effective_user.id)
        tasks = self.user_tasks.get(user_id, [])

        if not tasks:
            self._reply_with_keyboard(update, "🗒️ Your task list is empty.")
            return ConversationHandler.END

        message = "\n".join([f"{i + 1}. {t}" for i, t in enumerate(tasks)])
        self._reply_with_keyboard(update, "📝 Your Tasks:\n" + message)
        return ConversationHandler.END

    def delete_task(self, update: Update, context: CallbackContext):
        """
        Initiates the task deletion conversation, asking the user for the task number.
        """
        user_id = str(update.effective_user.id)
        tasks = self.user_tasks.get(user_id, [])

        if not tasks:
            self._reply_with_keyboard(update, "🗒️ Your task list is empty.")
            return ConversationHandler.END

        message = "📝 Your Tasks:\n" + "\n".join([f"{i + 1}. {t}" for i, t in enumerate(tasks)])
        self._reply_with_keyboard(
            update,
            f"{message}\n\nPlease send the number of the task to delete:",
            cancel_button=True
        )
        return DELETING_TASK

    def deleting_task(self, update: Update, context: CallbackContext):
        """
        Receives the task number from the user and deletes the corresponding task.
        """
        user_id = str(update.effective_user.id)
        tasks = self.user_tasks.get(user_id, [])
        text = update.message.text

        if text.lower() == "cancel":
            self._reply_with_keyboard(update, "❌ Task deletion canceled.")
            return ConversationHandler.END

        if not text.isdigit():
            self._reply_with_keyboard(update, "⚠️ Please send only the task number.")
            return DELETING_TASK

        index = int(text) - 1
        if 0 <= index < len(tasks):
            removed = tasks.pop(index)
            self._save_tasks()
            self._reply_with_keyboard(update, f"🗑️ Removed task: {removed}")
        else:
            self._reply_with_keyboard(update, "❌ Invalid task number. Please try again.")
            return DELETING_TASK

        return ConversationHandler.END

    def help_command(self, update: Update, context: CallbackContext):
        """
        Provides help information to the user.
        """
        self._reply_with_keyboard(
            update,
            "ℹ️ How to use this bot:\n"
            "- Click /add then send your task\n"
            "- Click /list to see all tasks\n"
            "- Click /delete then send task number"
        )
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext):
        """
        Cancels the current operation.
        """
        self._reply_with_keyboard(update, "❌ Operation canceled.")
        return ConversationHandler.END

    def run(self):
        """
        Sets up and runs the Telegram bot.
        """
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('add', self.add_task),
                CommandHandler('delete', self.delete_task)
            ],
            states={
                ADDING_TASK: [MessageHandler(Filters.text & ~Filters.command, self.adding_task)],
                DELETING_TASK: [MessageHandler(Filters.text & ~Filters.command, self.deleting_task)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(conv_handler)
        dp.add_handler(CommandHandler("list", self.list_tasks))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.help_command))

        updater.start_polling()
        updater.idle()

if __name__ == '__main__':
    bot = TodoBot()
    bot.run()
