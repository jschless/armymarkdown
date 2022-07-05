worker: celery -A app.celery worker --loglevel=info
web: gunicorn app:app -w 10 -t 