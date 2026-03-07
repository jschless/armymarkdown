FROM ubuntu:22.04

# Install system dependencies (no MS fonts needed - using Lato)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv curl git \
    fontconfig \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    latexmk \
    xz-utils \
    # Add supervisor for running multiple processes
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install additional LaTeX packages including Lato font
RUN tlmgr init-usertree && \
    tlmgr option repository https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2021/tlnet-final && \
    tlmgr install koma-script etoolbox xkeyval \
        xcolor datetime fmtcount background csquotes \
        pgf enumitem setspace booktabs \
        microtype pdftexcmds infwarerr everypage ragged2e \
        lato fontaxes mweights tools

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
