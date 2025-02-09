FROM python:3.11-alpine
WORKDIR /app
COPY src/pipeline/producer/ .
COPY ../../data/ .
RUN pip install kafka-python-ng pandas python-dotenv
CMD ["python", "producer.py"]
