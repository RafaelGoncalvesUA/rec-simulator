FROM rafego16/pipeline-custom-image:latest AS base
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    python3.9 \
    python3-pip && \
    apt clean && rm -rf /var/lib/apt/lists/

COPY --from=base /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=base /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
ENV PYTHONPATH="/usr/local/lib/python3.9/site-packages:$PYTHONPATH"

# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
#     ln -s /usr/bin/python3.9 /usr/bin/python

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y git
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .

# docker build -t rafego16/pipeline-custom-image-train:latest .
# docker push rafego16/pipeline-custom-image-train:latest
