# import bot
from .celeryinit import app as celery_app

__all__ = ("celery_app",)
