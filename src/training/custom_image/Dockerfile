FROM registry.localhost/pipeline-custom-image-builder:latest AS builder
FROM python:3.11-slim

COPY --from=builder /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

RUN python3 -m pip install python-dotenv

# docker build -t registry.localhost/pipeline-custom-image:latest .
# docker push registry.localhost/pipeline-custom-image:latest

# pull image in all nodes
