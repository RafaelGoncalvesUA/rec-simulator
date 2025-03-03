FROM python:3.11-alpine
WORKDIR /app
COPY . .
RUN pip install pandas requests python-dotenv
CMD ["python", "producer.py"]
