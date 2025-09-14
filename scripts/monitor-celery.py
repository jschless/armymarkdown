#!/usr/bin/env python3
"""
Simple Celery monitoring script
Run with: python monitor-celery.py
"""

import subprocess
import time


def check_celery_status():
    try:
        # Get active tasks
        result = subprocess.run(
            ["celery", "-A", "app.celery", "inspect", "active"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"[{time.strftime('%H:%M:%S')}] Active tasks:", result.stdout)

        # Get registered tasks
        result = subprocess.run(
            ["celery", "-A", "app.celery", "inspect", "registered"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"[{time.strftime('%H:%M:%S')}] Registered tasks:", result.stdout)

    except Exception as e:
        print(f"Error checking Celery: {e}")


if __name__ == "__main__":
    while True:
        check_celery_status()
        time.sleep(30)  # Check every 30 seconds
