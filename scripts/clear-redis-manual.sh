#!/bin/bash

# Manual Redis queue clearing script
echo "🧹 Manually clearing Redis queues..."

# Check if containers are running
if ! docker compose ps | grep -q "redis.*Up"; then
    echo "❌ Redis container is not running. Starting Redis..."
    docker compose up -d redis
    echo "⏳ Waiting for Redis to be ready..."
    sleep 5
fi

# Run the Python clearing script
if python3 clear-redis.py; then
    echo "✅ Redis queues cleared successfully"
    echo "🚀 Ready for fresh tasks!"
else
    echo "❌ Failed to clear Redis queues"
    echo "Make sure Redis is accessible and the Python script is working"
    exit 1
fi

echo "📊 Current Redis status:"
docker compose exec redis redis-cli info keyspace
