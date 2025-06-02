FROM rafego16/rl-agent-server
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "producer.py"]
