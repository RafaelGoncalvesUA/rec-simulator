FROM rafego16/pipeline-custom-image:latest AS base
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# add repository
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa -y

# export timezone - for python3.9 install
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    python3.9 python3.9-venv python3.9-distutils python3.9-dev && \
    apt clean && rm -rf /var/lib/apt/lists/

# copy packages from base image
COPY --from=base /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"
COPY --from=base /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
ENV PYTHONPATH="/usr/local/lib/python3.9/site-packages:$PYTHONPATH"

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
    ln -s /usr/bin/python3.9 /usr/bin/python && \
    apt-get remove -y python3.10

# install pip
RUN apt-get update && apt-get install -y python3-pip

COPY requirements.txt .
RUN apt-get install -y git && pip3 install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .

# docker build -t rafego16/pipeline-custom-image-train:latest .
# docker push rafego16/pipeline-custom-image-train:latest
