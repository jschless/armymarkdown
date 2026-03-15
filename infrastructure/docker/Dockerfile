FROM ubuntu:22.04

# Accept MS fonts EULA for Arial
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections
ENV TYPST_VERSION=0.14.2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv curl git \
    fontconfig ttf-mscorefonts-installer \
    xz-utils \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Typst binary used by the standalone armymemo package
RUN curl -L "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" -o /tmp/typst.tar.xz && \
    tar -xJf /tmp/typst.tar.xz -C /tmp && \
    install -m 0755 /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/typst && \
    rm -rf /tmp/typst.tar.xz /tmp/typst-x86_64-unknown-linux-musl

# Pre-warm font cache for faster first compilation
RUN fc-cache -fv && typst --version

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv --version
ENV PATH="/root/.local/bin:$PATH"

# Python configuration
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create data directory for SQLite databases
RUN mkdir -p /data

# Ensure resources directory is accessible
ENV APP_ROOT=/app

# Copy supervisor configuration
COPY infrastructure/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose HTTP port (Caddy handles SSL termination)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start both Gunicorn and Huey consumer via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
