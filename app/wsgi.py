from __init__ import create_app

app = create_app()
celery_app = app.extensions["celery"]

