

FROM debian:bullseye-slim

# Install any required packages
RUN apt update && apt install -y bash curl

# Copy your script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run it when container starts
CMD ["/start.sh"]