# Use a Linux base image
FROM ubuntu:latest

# Install necessary packages

# mscorefonts EULA
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip git \
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

RUN export OSFONTDIR=/usr/share/fonts
RUN luaotfload-tool -vvv --update --force

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your application files (if any)
COPY . /app

# Set working directory
WORKDIR /app

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0", "-w", "4", "app:app"]