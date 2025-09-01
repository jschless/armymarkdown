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

3. Run with docker-compose:
   ```bash
   docker-compose -f docker-compose-dev.yaml up
   ```

### Production Setup

1. Set environment variables on your production server:
   ```bash
   export FLASK_SECRET="your-production-secret"
   export RECAPTCHA_PUBLIC_KEY="your-recaptcha-public-key"
   # ... etc
   ```

2. Or use a `.env` file (make sure it's not in version control):
   ```bash
   docker-compose up
   ```

### Security Notes

- Never commit actual secrets to version control
- Use strong, randomly generated values for FLASK_SECRET
- Consider using Docker secrets or external secret management for production
- The `.env` file is already in `.gitignore` to prevent accidental commits

### Migration from local_config.py

If you were previously using `local_config.py`, you can convert it by:
1. Setting each key from your config dictionary as an environment variable
2. Removing the `local_config.py` file
3. Testing that the application starts correctly with the new environment variables