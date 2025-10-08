import os
import json
import time

JOBS_FILE = "jobs.txt"

def _read_file():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _write_file(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f)

def load_jobs():
    return _read_file()

def save_jobs(jobs):
    _write_file(jobs)

def add_job(chat_id, job_dict):
    jobs = _read_file()
    jobs.setdefault(str(chat_id), []).append(job_dict)
    _write_file(jobs)

def remove_job(chat_id, job_name):
    jobs = _read_file()
    job_list = jobs.get(str(chat_id), [])
    jobs[str(chat_id)] = [j for j in job_list if j["name"] != job_name]
    if not jobs[str(chat_id)]:
        jobs.pop(str(chat_id))
    _write_file(jobs)

def remove_all_jobs_file(chat_id):
    jobs = _read_file()
    if str(chat_id) in jobs:
        jobs.pop(str(chat_id))
        _write_file(jobs)

