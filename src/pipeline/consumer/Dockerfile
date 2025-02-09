FROM python:3.11-alpine
WORKDIR /app
COPY . .
RUN pip install kafka-python-ng pandas minio python-dotenv
CMD ["python", "consumer.py"]
