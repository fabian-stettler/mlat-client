#!/bin/bash
set -e

# Environment Variables mit Defaults
MLAT_SERVER="${MLAT_SERVER:-mlat1.adsbexchange.com:40900}"
MLAT_USER="${MLAT_USER:-your-username}"
LATITUDE="${LATITUDE:-0.0}"
LONGITUDE="${LONGITUDE:-0.0}"
ALTITUDE="${ALTITUDE:-0}"

echo "Starting ADS-B Processing Container"
echo "Server: $MLAT_SERVER"
echo "Position: LAT=$LATITUDE, LON=$LONGITUDE, ALT=$ALTITUDE"

# Prüfe ob USB Device verfügbar
if [ ! -e "/dev/bus/usb" ]; then
    echo "WARNING: USB device not found at /dev/bus/usb"
fi

# Starte dump1090
echo "Starting dump1090..."
gosu mlatuser dump1090 \
    --interactive \
    --net \
    --net-http-port 8080 \
    --net-ro-port 30005 \
    --quiet &
DUMP1090_PID=$!

# Warte bis dump1090 läuft
sleep 10

# Starte mlat-client
echo "Starting mlat-client..."
gosu mlatuser mlat-client \
    --input-type dump1090 \
    --input-connect localhost:30005 \
    --server "$MLAT_SERVER" \
    --user "$MLAT_USER" \
    --lat "$LATITUDE" \
    --lon "$LONGITUDE" \
    --alt "$ALTITUDE" \
    --results beast,connect,localhost:30004 \
    "$@" &
MLAT_PID=$!

# Health Check Funktion
health_check() {
    while true; do
        if ! kill -0 $DUMP1090_PID 2>/dev/null; then
            echo "dump1090 process died, exiting..."
            exit 1
        fi
        if ! kill -0 $MLAT_PID 2>/dev/null; then
            echo "mlat-client process died, exiting..."
            exit 1
        fi
        sleep 30
    done
}

# Starte Health Check im Hintergrund
health_check &

# Warte auf Prozesse
wait $DUMP1090_PID $MLAT_PID