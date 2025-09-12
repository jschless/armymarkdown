#!/usr/bin/env python3
"""
Clear Redis queues and failed tasks to start fresh.
Useful when redeploying after LaTeX compilation issues.
"""

import os
import sys

import redis


def clear_redis_queues():
    """Clear all Celery queues and failed tasks from Redis."""
    try:
        # Connect to Redis using environment variable or default
        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        print(f"Connecting to Redis at: {redis_url}")

        r = redis.from_url(redis_url)

        # Test connection
        r.ping()
        print("✅ Connected to Redis successfully")

        # Get all keys
        all_keys = r.keys("*")
        print(f"Found {len(all_keys)} total keys in Redis")

        # Clear Celery-related keys
        celery_patterns = [
            "celery-task-meta-*",  # Task results
            "_kombu.binding.*",  # Kombu bindings
            "celery",  # Default queue
            "create_memo",  # Our specific task queue
            "unacked*",  # Unacknowledged tasks
            "reserved*",  # Reserved tasks
        ]

        cleared_count = 0
        for pattern in celery_patterns:
            keys = r.keys(pattern)
            if keys:
                deleted = r.delete(*keys)
                cleared_count += deleted
                print(f"🗑️  Cleared {deleted} keys matching pattern: {pattern}")

        # Clear any remaining failed task states
        failed_keys = r.keys("celery-task-meta-*")
        if failed_keys:
            deleted = r.delete(*failed_keys)
            cleared_count += deleted
            print(f"🗑️  Cleared {deleted} failed task metadata")

        # Clear the default Celery queue
        queue_length = r.llen("celery")
        if queue_length > 0:
            r.delete("celery")
            cleared_count += 1
            print(f"🗑️  Cleared main celery queue ({queue_length} tasks)")

        print(f"✅ Successfully cleared {cleared_count} Redis keys")
        print("🚀 Redis is now clean and ready for fresh tasks")

    except redis.ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("Make sure Redis is running and accessible")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error clearing Redis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🧹 Clearing Redis queues and failed tasks...")
    clear_redis_queues()
