FROM python:3.11-alpine
WORKDIR /app
COPY . .
RUN pip install pandas requests
CMD ["python", "producer.py"]
