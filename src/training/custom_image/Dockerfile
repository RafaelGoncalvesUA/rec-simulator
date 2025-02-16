FROM python:3.11-alpine AS builder

# Install compiler and build tools
RUN apk add --no-cache \
        build-base \
        cmake \
        g++ \
        curl

# Install Rust using rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install the required Rust version
RUN rustup install 1.84.0 && rustup default 1.84.0

# Install python-microgrid from the GitHub repository (already includes numpy, pandas, gym, pyyaml, ...)
RUN wget https://github.com/ahalev/python-microgrid/archive/master.zip && \
    unzip master.zip && \
    rm -rf master.zip && \
    cd python-microgrid-master && \
    pip install .

# Clean up all build files
RUN apk del build-base cmake g++ curl && \
    rm -rf /root/.cargo/registry /root/.cargo/git /root/.rustup && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache/pip

FROM python:3.11-alpine

COPY --from=builder /root/.cargo/bin /root/.cargo/bin
ENV PATH="/root/.cargo/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

RUN apk add libgcc libstdc++

RUN python3 -m pip install python-dotenv

# docker build -t pipeline-custom-image .