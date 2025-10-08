import uuid
import time
from logging import Logger
from telegram import Update
from telegram.ext import ContextTypes, Application
import StarTechScraper as scrap
from fileHandler import load_jobs, add_job, remove_job, remove_all_jobs_file

# 🔔 Alarm callback
async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    seconds = job.data["due"]
    url = job.data["url"]

    message = f"⏰ Timer done! ({seconds} seconds)"
    info = scrap.get_price(url)
    if info:
        message += f"\n\033[1m Product:\033[0m {info['product']}\n\033[1m Price:\033[0m {info['price']}"
    else:
        message += "\n⚠️ Could not fetch product info."

    await context.bot.send_message(chat_id=chat_id, text=message)

# 👋 Start/help command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Use /set <seconds> <url> to set a timer.\n"
        "Use /listall to see active timers.\n"
        "Use /unset <index> to remove a timer.\n"
        "Use /unsetall to remove all timers."
    )

# ⏱️ Set a new timer
async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    try:
        due = float(context.args[0])
        url = context.args[1]
        if due < 0:
            await update.effective_message.reply_text("❌ Cannot set a timer in the past.")
            return

        job_name = f"{chat_id}_{uuid.uuid4().hex}"
        context.job_queue.run_repeating(
            alarm,
            interval=due,
            first=due,
            chat_id=chat_id,
            name=job_name,
            data={"due": due, "url": url}
        )

        job_dict = {"name": job_name, "due": due, "url": url, "start": time.time()}
        add_job(chat_id, job_dict)

        await update.effective_message.reply_text(f"✅ Timer set for \033[1m{due} seconds\033[0m.\nURL: {url}")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds> <url>")

# 📋 List all active timers
async def listall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    jobs = load_jobs()
    print(jobs)
    job_list = jobs.get(chat_id, [])
    print("Job List\n")
    if not job_list:
        await update.message.reply_text("You have no active timers.")
        return

    text = "⏰ Active timers:\n"
    for i, job in enumerate(job_list, start=1):
        text += f"{i}. {job['due']}s → {job['url']}\n"
    await update.message.reply_text(text)

# ❌ Remove a specific timer
async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    jobs = load_jobs()
    job_list = jobs.get(chat_id, [])

    try:
        index = int(context.args[0]) - 1
        job_to_remove = job_list[index]
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unset <index>")
        return
    except Exception:
        await update.message.reply_text("❌ Invalid index.")
        return

    remove_job(chat_id, job_to_remove["name"])
    for job in context.job_queue.get_jobs_by_name(job_to_remove["name"]):
        job.schedule_removal()

    await update.message.reply_text(
        f"✅ Timer {index+1} cancelled ({job_to_remove['due']}s → {job_to_remove['url']})."
    )

# 🧹 Remove all timers
async def unsetall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    for job in context.job_queue.jobs():
        if job.name.startswith(f"{chat_id}_"):
            job.schedule_removal()

    remove_all_jobs_file(chat_id)
    await update.message.reply_text("✅ All timers cancelled!")


# Rehydrate jobs_queue on startup:
def rehydrate_jobs(application: Application, alarm_callback):
    jobs = load_jobs()
    for chat_id, job_list in jobs.items():
        for job in job_list:
            application.job_queue.run_repeating(
                alarm_callback,
                interval=job["due"],
                first = 0,
                chat_id=int(chat_id),
                name=job["name"],
                data={"due": job["due"], "url": job["url"]}
            )