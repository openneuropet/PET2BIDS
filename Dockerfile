FROM python:3.11-slim

LABEL maintainer="OpenNeuroPET team"
LABEL description="PET2BIDS"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    cmake \
    build-essential \
    pkg-config \
    libturbojpeg0-dev \
    libopenjp2-7-dev \
    libjpeg-dev \
    libcharls-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
# Build and install dcm2niix
RUN git clone https://github.com/rordenlab/dcm2niix.git && \
    cd dcm2niix && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DZLIB_IMPLEMENTATION=Cloudflare -DUSE_JPEGLS=ON -DUSE_OPENJPEG=ON .. && \
    make && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/dcm2niix

# Verify dcm2niix installation and ensure it's in PATH
RUN which dcm2niix && dcm2niix -h
ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /out
# Install pypet2bids
RUN pip install pypet2bids