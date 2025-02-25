FROM python:3.11-slim

# Install compiler and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    curl

# Install Rust using rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install the required Rust version
RUN rustup install 1.84.0 && rustup default 1.84.0

# Install python-microgrid from the GitHub repository (already includes numpy, pandas, gym, pyyaml, ...)
RUN apt-get install wget unzip -y && \
    wget https://github.com/ahalev/python-microgrid/archive/master.zip && \
    unzip master.zip && \
    rm -rf master.zip && \
    cd python-microgrid-master && \
    pip install .

# Clean up all build files
RUN apt-get remove build-essential cmake g++ curl -y && \
    rm -rf /root/.cargo/registry /root/.cargo/git /root/.rustup && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache/pip

# docker build -t registry.localhost/pipeline-custom-image-builder:latest .
# docker push registry.localhost/pipeline-custom-image-builder:latest