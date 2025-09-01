#!/bin/bash

# Army Memo Maker Deployment Script
echo "🚀 Starting deployment..."

# Pull latest changes
echo "📥 Pulling latest changes from main branch..."
git pull origin main

# Stop existing containers
echo "⏹️  Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start containers
echo "🏗️  Building and starting containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Clean up unused images
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

echo "✅ Deployment complete!"
echo "🌐 Application should be running at your domain"

# Check container status
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps