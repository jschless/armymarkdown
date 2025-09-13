FROM ubuntu:22.04

RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv curl git \
    fontconfig ttf-mscorefonts-installer \
    texlive-base \
    texlive-latex-base \
    texlive-luatex \
    latexmk \
    xz-utils

RUN fc-cache -f -v

RUN tlmgr init-usertree
RUN tlmgr option repository ftp://tug.org/historic/systems/texlive/2021/tlnet-final
RUN tlmgr install koma-script etoolbox fontspec xkeyval \
    		  xcolor datetime fmtcount background csquotes \
		  pgf background enumitem setspace booktabs \
		  microtype pdftexcmds infwarerr everypage ragged2e

# Set font directory and build font cache for LuaLaTeX
ENV OSFONTDIR=/usr/share/fonts
RUN fc-cache -fv
RUN luaotfload-tool --update --quiet --force
# Verify Arial font is available
RUN fc-match Arial && luaotfload-tool --find=Arial

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv --version
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

CMD uv run gunicorn -w 3 --certfile /etc/letsencrypt/live/armymemomaker.com/fullchain.pem --keyfile /etc/letsencrypt/live/armymemomaker.com/privkey.pem -b 0.0.0.0:8443 -t 360 app.main:app