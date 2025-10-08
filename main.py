#!/usr/bin/env python
# pylint: disable=unused-argument

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler
from commands import alarm, start, set_timer, listall, unset, unsetall, rehydrate_jobs

# 🌱 Load environment variables
load_dotenv()
token = os.getenv("BOT_TOKEN")

# 🧾 Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main() -> None:
    # 🤖 Initialize bot application
    application = Application.builder().token(token).build()
    # 🔁 Restore jobs from file
    rehydrate_jobs(application, alarm)
    # 📦 Register command handlers
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("listall", listall))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("unsetall", unsetall))

    # 🚀 Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
