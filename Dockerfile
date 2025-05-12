FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    fzf \
    nodejs \
    ffmpeg \
    openssl \
    git \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot files
COPY . .

# Set correct permissions for the script
RUN chmod +x /app/animepahe-dl.sh \
    && chmod 755 /app/animepahe-dl.sh \
    && chown root:root /app/animepahe-dl.sh

# Create downloads directory with proper permissions
RUN mkdir -p /app/downloads \
    && chmod 777 /app/downloads

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python3", "bot.py"]