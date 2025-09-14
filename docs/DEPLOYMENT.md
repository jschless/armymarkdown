# Deployment Guide

## Environment Variables Setup

This application now uses environment variables instead of a local configuration file for better security and deployment practices.

### Required Environment Variables

1. **FLASK_SECRET** - Secret key for Flask sessions and CSRF protection
2. **RECAPTCHA_PUBLIC_KEY** - Google reCAPTCHA public key
3. **RECAPTCHA_PRIVATE_KEY** - Google reCAPTCHA private key
4. **REDIS_URL** - Redis connection URL (defaults to `redis://redis:6379/0`)
5. **AWS_ACCESS_KEY_ID** - AWS access key for S3 storage
6. **AWS_SECRET_ACCESS_KEY** - AWS secret key for S3 storage

### Development Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual values in the `.env` file

3. Run with Make commands:
   ```bash
   make docker-dev-build
   ```

### Production Setup

1. Set environment variables on your production server:
   ```bash
   export FLASK_SECRET="your-production-secret"
   export RECAPTCHA_PUBLIC_KEY="your-recaptcha-public-key"
   # ... etc
   ```

2. Deploy with Docker:
   ```bash
   make docker-prod
   # or manually:
   # docker compose -f infrastructure/compose/docker-compose.yaml up --build -d
   ```

### Security Notes

- Never commit actual secrets to version control
- Use strong, randomly generated values for FLASK_SECRET
- Consider using Docker secrets or external secret management for production
- The `.env` file is already in `.gitignore` to prevent accidental commits

## Docker Deployment

### Development Environment

```bash
# Build and start all services
make docker-dev-build

# Services included:
# - Flask app (port 8000)
# - Celery worker
# - Redis
# - SQLite database
```

### Production Environment

```bash
# Build and start production services
make docker-prod

# Services included:
# - Flask app with Gunicorn
# - Celery worker
# - Redis
# - Nginx (if configured)
# - SSL termination (if configured)
```

### Container Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │────│   Celery Worker │    │   Redis Queue   │
│   (Gunicorn)    │    │   (PDF Gen)     │    │   (Port 6379)   │
│   (Port 8000)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────┐
                    │   SQLite DB     │
                    │   (Volume)      │
                    └─────────────────┘
```

## Database Management

### Automatic Migration

The application includes automatic database schema migration:
- On startup, checks for required tables and columns
- Automatically creates missing tables
- Migrates schema if needed (e.g., adding `created_at` column)
- Uses file locking to prevent race conditions between workers

### Manual Database Operations

```bash
# Access database in Docker container
docker compose exec flask_app sqlite3 /data/users.db

# Backup database
docker compose exec flask_app cp /data/users.db /tmp/backup.db

# View database logs
docker compose logs flask_app | grep -i database
```

## Monitoring and Logging

### Application Logs

```bash
# View Flask app logs
docker compose logs -f flask_app

# View Celery worker logs
docker compose logs -f celery

# View all service logs
docker compose logs -f
```

### Health Checks

- Flask app: `GET /` should return 200
- Redis: Check container status
- Database: Application logs show successful connection

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 6379 are available
2. **Environment variables**: Check `.env` file exists and is readable
3. **Database permissions**: Ensure `/data` volume has correct permissions
4. **LaTeX compilation**: Check container has LaTeX packages installed

### Debug Commands

```bash
# Check container status
docker compose ps

# Enter container shell
docker compose exec flask_app bash

# Check environment variables
docker compose exec flask_app env

# Test database connection
docker compose exec flask_app python -c "from db.schema import db; print('DB OK')"
```

### Migration from local_config.py

If you were previously using `local_config.py`, you can convert it by:
1. Setting each key from your config dictionary as an environment variable
2. Removing the `local_config.py` file
3. Testing that the application starts correctly with the new environment variables
