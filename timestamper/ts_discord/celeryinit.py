from celery import Celery

print("LOADING CELERY - JP")
app = Celery('timestamper.ts_discord.bot'
             # , task_cls=celery_longterm_scheduler.Task
             , broker='redis://'
             )
default_config = 'timestamper.ts_discord.celeryconfig'
# default_config = './celeryconfig'
app.config_from_object(default_config, )
# app.autodiscover_tasks('timestamper.ts_discord.bot')
from timestamper.ts_discord import bot

app.register_task(bot.do_reminder)
