


FROM alpine:latest

# Install bash or any needed tool
RUN apk add --no-cache bash curl

# Copy script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run the script
CMD ["/start.sh"]