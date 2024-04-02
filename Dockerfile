# Use a Linux base image
FROM ubuntu:latest

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    redis-server \
#    texlive-full \
#    texlive-xetex \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Get Arial font 
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections
RUN apt-get update && apt-get install -y --no-install-recommends fontconfig ttf-mscorefonts-installer
    # ADD localfonts.conf /etc/fonts/local.conf
RUN fc-cache -f -v

# Install LATEX
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-base \
    texlive-latex-base \
    texlive-luatex \
    latexmk \
    xz-utils

RUN tlmgr init-usertree
RUN tlmgr option repository ftp://tug.org/historic/systems/texlive/2021/tlnet-final
RUN tlmgr install koma-script etoolbox fontspec xkeyval \
    	  	  xcolor datetime fmtcount background csquotes \
		  pgf background enumitem setspace booktabs \
		  microtype pdftexcmds infwarerr everypage ragged2e

RUN export OSFONTDIR=/usr/share/fonts
RUN luaotfload-tool -vvv --update --force


# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy your application files (if any)
COPY . /app

# Set working directory
WORKDIR /app

# Install Python dependencies (if any)
RUN pip install -r requirements.txt

# Command to run the application
CMD ["flask", "run", "--host", "0.0.0.0"]