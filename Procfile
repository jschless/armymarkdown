worker: celery -A app.celery worker --loglevel=info
web: gunicorn -w 6 app:app 