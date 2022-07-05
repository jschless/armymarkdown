worker: celery -A app.celery worker --loglevel=info
web: gunicorn -w 10 app:app 