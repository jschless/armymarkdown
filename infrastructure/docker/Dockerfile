FROM ubuntu:22.04

RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip curl git \
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

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

# Create a virtual environment using Python 3.11
RUN python3.11 -m venv /.venv
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

# Upgrade pip and install basic tools
RUN pip install --upgrade pip setuptools wheel

COPY pyproject.toml ./

# Extract dependencies from pyproject.toml and install with pip
RUN pip install \
    boto3==1.40.27 \
    celery==5.5.3 \
    email-validator==2.3.0 \
    flask==3.1.2 \
    flask-login==0.6.3 \
    flask-sqlalchemy==3.1.1 \
    flask-talisman==1.1.0 \
    flask-wtf==1.2.2 \
    gunicorn==23.0.0 \
    language-tool-python==2.9.4 \
    pandas==2.3.2 \
    python-dateutil==2.9.0.post0 \
    python-dotenv==1.1.1 \
    redis==6.4.0 \
    requests==2.32.5 \
    sqlalchemy==2.0.43 \
    tabulate==0.9.0 \
    wtforms==3.2.1

COPY . /app

WORKDIR /app

# Install the local package
RUN pip install -e .

CMD gunicorn -w 3 --certfile /etc/letsencrypt/live/armymemomaker.com/fullchain.pem --keyfile /etc/letsencrypt/live/armymemomaker.com/privkey.pem -b 0.0.0.0:8443 -t 360 --reload app:app