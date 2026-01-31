"""
Config package initialization.

This imports the Celery app so that it's loaded when Django starts.
"""
try:
    from config.celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed - skip (for development/migrations without celery)
    celery_app = None
    __all__ = ()
