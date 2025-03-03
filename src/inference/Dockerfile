FROM rafego16/pipeline-custom-image-train:latest

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# (test dockerised environment) ENTRYPOINT ["tail", "-f", "/dev/null"]

EXPOSE 8080
CMD ["python", "server.py"]

# docker build -t rafego16/rl-agent-server .
# docker push rafego16/rl-agent-server