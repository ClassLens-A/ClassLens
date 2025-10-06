from .celery import app as celery_app
__all__ = ('celery_app')
print("Hey There app is loaded:", __all__)