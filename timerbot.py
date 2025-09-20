#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
import StarTechScraper as scrap
import uuid
import time
import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("BOT_TOKEN")

JOBS_FILE = "jobs.txt"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load jobs from file
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    with open(JOBS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Save jobs to file
def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f)

# Add a job to file
def add_job(chat_id, job_dict):
    jobs = load_jobs()
    jobs.setdefault(str(chat_id), [])
    jobs[str(chat_id)].append(job_dict)
    save_jobs(jobs)

# Remove a specific job from file
def remove_job(chat_id, job_name):
    jobs = load_jobs()
    if str(chat_id) in jobs:
        jobs[str(chat_id)] = [j for j in jobs[str(chat_id)] if j["name"] != job_name]
        if not jobs[str(chat_id)]:
            jobs.pop(str(chat_id))
        save_jobs(jobs)

# Remove all jobs for a chat
def remove_all_jobs_file(chat_id):
    jobs = load_jobs()
    if str(chat_id) in jobs:
        jobs.pop(str(chat_id))
        save_jobs(jobs)

# Track timers in memory for quick access
user_jobs = load_jobs()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Use /set <seconds> <url> to set a timer.\n"
        "Use /listall to see active timers.\n"
        "Use /unset <index> to remove a timer.\n"
        "Use /unsetall to remove all timers."
    )


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    seconds = job.data["due"]
    url = job.data["url"]

    message = f"⏰ Timer done! ({seconds} seconds)"
    if url:
        info = scrap.get_price(url)
        if info:
            message += f"\nProduct: {info['product']}\nPrice: {info['price']}"
        else:
            message += "\n⚠️ Could not fetch product info."

    await context.bot.send_message(chat_id=chat_id, text=message)


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    try:
        due = float(context.args[0])
        url = context.args[1]
        if due < 0:
            await update.effective_message.reply_text("Sorry, cannot set a timer in the past!")
            return

        job_name = f"{chat_id}_{uuid.uuid4().hex}"


        context.job_queue.run_repeating(
            alarm, interval=due, first=due, chat_id=chat_id, name=job_name, data={"due": due, "url": url}
        )

        job_dict = {"name": job_name, "due": due, "url": url, "start": time.time()}
        user_jobs.setdefault(chat_id, []).append(job_dict)
        add_job(chat_id, job_dict)

        await update.effective_message.reply_text(f"⏰ Timer set for {due} seconds.\nURL: {url}")

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds> <url>")


async def listall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id not in user_jobs or not user_jobs[chat_id]:
        await update.message.reply_text("You have no active timers.")
        return

    text = "⏰ Active timers:\n"
    for i, job in enumerate(user_jobs[chat_id], start=1):
        elapsed = time.time() - job["start"]
        remaining = max(0, job["due"] - elapsed)
        text += f"{i}. {remaining:.1f}s → {job['url']}\n"

    await update.message.reply_text(text)


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    try:
        index = int(context.args[0]) - 1
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unset <index>")
        return

    if chat_id not in user_jobs or not user_jobs[chat_id]:
        await update.message.reply_text("❌ No active timers.")
        return

    if index < 0 or index >= len(user_jobs[chat_id]):
        await update.message.reply_text("❌ Invalid index.")
        return

    job_to_remove = user_jobs[chat_id].pop(index)
    remove_job(chat_id, job_to_remove["name"])
    current_jobs = context.job_queue.get_jobs_by_name(job_to_remove["name"])
    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_text(
        f"✅ Timer {index+1} cancelled ({job_to_remove['due']}s → {job_to_remove['url']})."
    )


async def unsetall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    current_jobs = [job for job in context.job_queue.jobs() if job.name.startswith(f"{chat_id}_")]
    for job in current_jobs:
        job.schedule_removal()

    if chat_id in user_jobs:
        user_jobs.pop(chat_id)
        remove_all_jobs_file(chat_id)

    await update.message.reply_text("✅ All timers cancelled!")


def main() -> None:
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("listall", listall))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("unsetall", unsetall))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
