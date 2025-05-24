


FROM python:3.10-alpine

RUN apk add --no-cache bash

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN chmod +x start.sh

CMD ["python", "bot.py"]