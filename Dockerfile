# Use a Linux base image
FROM ubuntu:latest

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    redis-server \
    texlive \
    texlive-xetex \
    latexmk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy your application files (if any)
COPY . /app

# Set working directory
WORKDIR /app

RUN cp ./Arial /usr/local/share/fonts 

# Install Python dependencies (if any)
RUN pip install -r requirements.txt

# Command to run the application
CMD ["flask", "run", "--host", "0.0.0.0"]