from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os

os.makedirs("data", exist_ok=True)
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///data/jobs.sqlite')}
job_defaults = {
    'misfire_grace_period': 86400
}
scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults, timezone="Asia/Tashkent")