FROM registry.localhost/pipeline-custom-image:latest AS base
RUN pip install --default-timeout=100 torch stable-baselines3 joblib

FROM python:3.11-slim

COPY --from=base /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

# docker build -t registry.localhost/pipeline-custom-image-train:latest .
# docker push registry.localhost/pipeline-custom-image-train:latest
