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
    lighttpd \
    wget \
    gzip \
    cron \
    net-tools \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fix lighttpd permissions issue: Use the /app directory for PID file
RUN sed -i '/server.pid-file/c\server.pid-file = "/app/lighttpd.pid"' /etc/lighttpd/lighttpd.conf

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

#start tar1090
RUN git clone https://github.com/wiedehopf/tar1090.git /usr/local/share/tar1090 && \
    /usr/local/share/tar1090/install.sh readsb

#create symlink from readsb directory to tar1090 html data directory
RUN ln -s /run/readsb /usr/local/share/tar1090/html/data

#set reading directory of lighttpd to correct dir
RUN sed -i 's|"/data/" => "readsb/"|"/data/" => "/run/readsb/"|' /etc/lighttpd/conf-available/*port.conf

# Erstelle User mit USB Zugriffsrechten
RUN useradd -m -r -s /bin/bash -G dialout mlatuser

# Kopiere EntryPoint und setze Berechtigungen
COPY entrypoint.sh /entrypoint.sh
COPY nginx.conf /etc/nginx/sites-enabled/default
RUN chmod +x /entrypoint.sh

EXPOSE 8080 30003 30004 30005
ENTRYPOINT ["/entrypoint.sh"]
