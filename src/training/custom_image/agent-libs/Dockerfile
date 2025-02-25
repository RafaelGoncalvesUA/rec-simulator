FROM registry.localhost/pipeline-custom-image:latest AS base
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    python3.11 \
    python3-pip && \
    apt clean && rm -rf /var/lib/apt/lists/

COPY --from=base /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    ln -s /usr/bin/python3.11 /usr/bin/python

RUN pip3 --no-cache-dir install torch --index-url https://download.pytorch.org/whl/cu118
RUN pip3 --no-cache-dir install stable-baselines3 joblib

WORKDIR /app
COPY . .

# docker build -t registry.localhost/pipeline-custom-image-train:latest .
# docker save registry.localhost/pipeline-custom-image-train:latest -o train.tar

# for all nodes: 
# scp train.tar <ip>:~/train.tar
# run the following command on the registry server: "docker load -i train.tar"