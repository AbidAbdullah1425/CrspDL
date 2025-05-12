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

COPY . .
RUN chmod +x animepahe-dl.sh

# Set environment variables
ENV ANIMEPAHE_DL_NODE=/usr/bin/node
ENV ANIMEPAHE_DL_NONINTERACTIVE=1

CMD ["python3", "main.py"]