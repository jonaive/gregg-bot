FROM python:3.8
ARG BOT_TOKEN
ARG DB_CONNECTION_STRING
ENV BOT_TOKEN=$BOT_TOKEN
ENV DB_CONNECTION_STRING=$DB_CONNECTION_STRING
WORKDIR /greg
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
