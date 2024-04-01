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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# RUN fc-cache -f

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy your application files (if any)
COPY . /app

RUN cp ./Arial /usr/local/share/fonts 

# Install Python dependencies (if any)
RUN pip install -r requirements.txt

# Expose ports (if any)
EXPOSE 8000

# Command to run the application
CMD [ "python", "app.py" ]