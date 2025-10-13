FROM python:3.9-slim-bullseye

LABEL maintainer="fabian.stettler@hispeed.ch"
LABEL description="mlat-client with dump1090 (readsb) for ADS-B processing"

# Build environment
FROM debian:bullseye-slim as builder

# Install build dependencies and RTL-SDR
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libusb-1.0-0-dev \
    librtlsdr-dev \
    libncurses-dev \
    zlib1g-dev \
    libzstd-dev \
    python3 \
    python3-pip \
    python3-dev \
    git \
    usbutils \
    rtl-sdr \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Klone und baue readsb (moderner dump1090-Ersatz mit besserer SBS-Unterstützung)
RUN git clone https://github.com/wiedehopf/readsb.git dump1090-src && \
    cd dump1090-src && \
    make RTLSDR=yes && \
    cp readsb /usr/local/bin/dump1090 && \
    ln -s /usr/local/bin/dump1090 /usr/local/bin/readsb && \
    cd /app && \
    rm -rf dump1090-src

# Klone mlat-client
RUN git clone https://github.com/wiedehopf/mlat-client.git . && \
    pip3 install setuptools pyasyncore && \
    python3 setup.py build && \
    python3 setup.py install

# Erstelle User mit USB Zugriffsrechten
RUN useradd -m -r -s /bin/bash -G dialout mlatuser

# Kopiere EntryPoint und setze Berechtigungen
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080 30003 30004 30005
ENTRYPOINT ["/entrypoint.sh"]