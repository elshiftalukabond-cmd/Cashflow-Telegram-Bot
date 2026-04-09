from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os

os.makedirs("data", exist_ok=True)
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///data/jobs.sqlite')}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Tashkent")