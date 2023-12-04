# CELERY_BROKER_URL = 'redis://localhost:6379/1'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_longterm_scheduler_backend = 'redis://localhost:6379/1'
longterm_scheduler_backend = 'redis://localhost:6379/1'
CELERY_LONGTERM_SCHEDULER_BACKEND = 'redis://localhost:6379/1'
# CELERY_IMPORTS = ('timestamper.ts_discord.bot')
broker_connection_retry_on_startup = True
