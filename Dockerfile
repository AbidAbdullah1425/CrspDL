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

# Copy script and make executable
COPY animepahe-dl.sh .
RUN chmod +x animepahe-dl.sh

# Copy all bot files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python3", "main.py"]
