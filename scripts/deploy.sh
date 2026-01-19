#!/bin/bash

# Army Memo Maker Deployment Script
# Simplified architecture: Flask + Huey + Caddy
# Uses Docker Hub images + Watchtower for zero-downtime deployments

set -e  # Exit on any error

# Parse command line arguments
DRY_RUN=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Show help
if [ "$HELP" = true ]; then
    echo "Army Memo Maker Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be done without executing"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "This script deploys using Docker Hub images + Watchtower for zero-downtime deployments"
    echo ""
    echo "Architecture:"
    echo "  - app: Flask + Gunicorn + Huey (single container)"
    echo "  - caddy: Reverse proxy with automatic SSL"
    echo "  - watchtower: Automatic container updates"
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    echo "🧪 DRY RUN MODE - No changes will be made"
fi

echo "🚀 Starting deployment with simplified architecture..."

# Configuration
COMPOSE_FILE="infrastructure/compose/docker-compose-production.yaml"
ENV_FILE=".env"

# Check if we're in the right directory
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found. Run this script from the project root."
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found. Please create environment file."
    exit 1
fi

# Function to check if container is healthy
check_health() {
    local service=$1
    echo "🔍 Checking health of $service..."

    for i in {1..30}; do
        if docker compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo "⏳ Waiting for $service to be healthy... ($i/30)"
        sleep 10
    done

    echo "❌ $service failed to become healthy"
    return 1
}

# Initial deployment or update
if [ "$DRY_RUN" = true ]; then
    echo "📋 DRY RUN: Would check if application is running"
    echo "📋 DRY RUN: Would pull latest images from Docker Hub"
    echo "📋 DRY RUN: Would start/restart services as needed"
    echo "📋 DRY RUN: Would wait for health checks to pass"
elif docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    echo "📦 Application is running. Watchtower will handle updates automatically."
    echo "ℹ️  To force an immediate update, trigger the GitHub Actions workflow."
else
    echo "🏗️  Initial deployment - pulling and starting containers..."

    # Pull latest images
    echo "📥 Pulling latest images from Docker Hub..."
    docker compose -f "$COMPOSE_FILE" pull --quiet

    # Start all services
    echo "🚀 Starting all services..."
    docker compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    echo "⏳ Waiting for services to become healthy..."
    check_health "app"

    echo "✅ Initial deployment complete!"
fi

# Clean up old images
if [ "$DRY_RUN" = true ]; then
    echo "📋 DRY RUN: Would clean up unused Docker images"
else
    echo "🧹 Cleaning up unused Docker images..."
    docker image prune -f
fi

# Show status
echo ""
if [ "$DRY_RUN" = true ]; then
    echo "📋 DRY RUN: Would show current service status"
else
    echo "📊 Current Status:"
    docker compose -f "$COMPOSE_FILE" ps
fi

echo ""
echo "🎯 Deployment Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$DRY_RUN" = true ]; then
    echo "📋 DRY RUN: Would deploy with Watchtower monitoring"
    echo "📋 DRY RUN: Auto-updates would be enabled (checks every 5 minutes)"
else
    echo "✅ Application: Running with Watchtower monitoring"
    echo "🔄 Auto-updates: Enabled (checks every 5 minutes)"
fi
echo "🐳 Images: Pulled from Docker Hub (jschless/armymarkdown-*)"
echo "📦 Services: app (Flask+Huey), caddy (reverse proxy)"
echo "🌐 URL: https://armymemomaker.com"
echo "📝 Logs: docker compose -f $COMPOSE_FILE logs -f [service]"
echo "🛑 Stop: docker compose -f $COMPOSE_FILE down"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Watchtower is running
if [ "$DRY_RUN" = true ]; then
    echo "📋 DRY RUN: Would check if Watchtower is monitoring for updates"
elif docker compose -f "$COMPOSE_FILE" ps watchtower | grep -q "Up"; then
    echo "✅ Watchtower is monitoring for updates"
else
    echo "⚠️  Watchtower is not running - automatic updates disabled"
fi

echo ""
echo "🔧 Next Steps:"
echo "1. Push changes to main branch to trigger new image builds"
echo "2. Watchtower will automatically deploy new images when available"
echo "3. Monitor logs: docker compose -f $COMPOSE_FILE logs -f"
