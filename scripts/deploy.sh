#!/bin/bash

# Army Memo Maker Deployment Script
echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest changes from main branch..."
git pull origin main

# Stop existing containers
echo "⏹️  Stopping existing containers..."
docker compose down

# Clear Redis queues before rebuilding to prevent old failed tasks from running
echo "🧹 Clearing Redis queues and failed tasks..."
# Start only Redis temporarily to clear it
docker compose up -d redis
sleep 5  # Wait for Redis to be ready

# Clear the queues using our Python script from within a container
if docker compose run --rm web python3 clear-redis.py; then
    echo "✅ Redis queues cleared successfully"
else
    echo "⚠️  Warning: Could not clear Redis queues, continuing anyway..."
fi

# Stop Redis before full rebuild
docker compose down

# Build and start containers
echo "🏗️  Building and starting containers..."
docker compose up --build -d

# Clean up unused images
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

echo "✅ Deployment complete!"
echo "🌐 Application should be running at your domain"

# Check container status
echo "📊 Container Status:"
docker compose ps
