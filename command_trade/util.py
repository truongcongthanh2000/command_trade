from telegram.ext import ContextTypes

seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000, "y": 31536000} # assume 1 month = 30days, 1 year = 365 days

def convert_to_seconds(s): # ex: 15m, 1s, 1y, 1M, ...
    return int(s[:-1]) * seconds_per_unit[s[-1]]

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True