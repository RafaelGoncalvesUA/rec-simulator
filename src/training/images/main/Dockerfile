FROM pipeline-custom-image-builder:latest AS builder
FROM python:3.11-slim

COPY --from=builder /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

RUN python3 -m pip install python-dotenv

# docker build -t rafego16/pipeline-custom-image:latest .
# docker push rafego16/pipeline-custom-image:latest
