FROM python:3.9-slim

# Install dependencies including nodejs
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    fzf \
    nodejs \
    ffmpeg \
    openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Make script executable
RUN chmod +x animepahe-dl.sh && \
    mkdir -p /tmp/downloads

# Set environment variable for script
ENV ANIMEPAHE_DL_NODE=/usr/bin/node

CMD ["python3", "main.py"]