FROM python:3.9-slim

# Install dependencies
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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files including the script
COPY . .
RUN chmod +x /app/animepahe-dl.sh

# Test script execution
RUN /app/animepahe-dl.sh -a "test" || true

CMD ["python3", "main.py"]