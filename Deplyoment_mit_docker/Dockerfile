FROM python:3.9-slim-bullseye

# Metadaten
LABEL maintainer="your-name@email.com"
LABEL description="mlat-client with dump1090 for Raspberry Pi"

# Installiere Abhängigkeiten
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    pkg-config \
    libusb-1.0-0-dev \
    librtlsdr-dev \
    && rm -rf /var/lib/apt/lists/*

# Setze Arbeitsverzeichnis
WORKDIR /app

# Klone und baue dump1090 (für USB Device Zugriff)
RUN git clone https://github.com/antirez/dump1090.git dump1090-src && \
    cd dump1090-src && \
    make && \
    cp dump1090 /usr/local/bin/ && \
    cd /app && \
    rm -rf dump1090-src

# Klone mlat-client
RUN git clone https://github.com/wiedehopf/mlat-client.git . && \
    pip3 install setuptools pyasyncore && \
    python3 setup.py build && \
    python3 setup.py install

# Erstelle User mit USB Zugriffsrechten
RUN useradd -m -r -s /bin/bash -G dialout mlatuser

# Installiere gosu für User-Switching
RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# Kopiere das entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose alle verwendeten Ports
EXPOSE 8080 30003 30004 30005

# Setze Entrypoint
ENTRYPOINT ["/entrypoint.sh"]