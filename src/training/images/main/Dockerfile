FROM pipeline-custom-image-builder:latest AS builder
FROM python:3.9-slim

COPY --from=builder /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

WORKDIR /app
COPY . .

RUN python3 -m pip install python-dotenv minio psycopg2-binary

# docker build -t rafego16/pipeline-custom-image:latest .
# docker push rafego16/pipeline-custom-image:latest
