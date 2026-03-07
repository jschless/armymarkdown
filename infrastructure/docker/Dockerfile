FROM ubuntu:22.04

# Accept MS fonts EULA for Arial
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv curl git \
    fontconfig ttf-mscorefonts-installer \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-luatex \
    latexmk \
    xz-utils \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install additional LaTeX packages
RUN tlmgr init-usertree && \
    tlmgr option repository https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2021/tlnet-final && \
    tlmgr install koma-script etoolbox fontspec xkeyval \
        xcolor datetime fmtcount background csquotes \
        pgf enumitem setspace booktabs \
        microtype pdftexcmds infwarerr everypage ragged2e tools

# Pre-warm font caches for faster first compilation
ENV OSFONTDIR=/usr/share/fonts
RUN fc-cache -fv && \
    luaotfload-tool --update --force && \
    chmod -R 755 /var/cache/fontconfig

# Pre-compile a test document to warm LuaTeX caches
RUN echo '\documentclass{article}\usepackage{fontspec}\setmainfont{Arial}\begin{document}test\end{document}' > /tmp/warmup.tex && \
    cd /tmp && lualatex --interaction=nonstopmode warmup.tex || true && \
    rm -f /tmp/warmup.*

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
