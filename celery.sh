#!/usr/bin/env bash


chown -R nobody:nogroup /app /root

exec celery -A app.celery worker -l info  --uid=nobody --gid=nogroup
