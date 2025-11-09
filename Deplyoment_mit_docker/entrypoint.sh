#!/bin/bash
set -euo pipefail

# Minimal entrypoint: start readsb and mlat-client to localhost.

# Config via env
MLAT_SERVER="${MLAT_SERVER:-localhost:40147}"
MLAT_USER="${MLAT_USER:-mlat-docker}"
LATITUDE="${LATITUDE:-0.0}"
LONGITUDE="${LONGITUDE:-0.0}"
ALTITUDE="${ALTITUDE:-0}"

# readsb options (Option A: run readsb in container on RTL-SDR)
READSB_DEVICE_TYPE="${READSB_DEVICE_TYPE:-rtlsdr}"
# Device selection: prefer READSB_DEVICE, else READSB_DEVICE_INDEX, else RTL_DEVICE_INDEX; empty means let readsb pick default
READSB_DEVICE="${READSB_DEVICE:-}"
if [[ -z "${READSB_DEVICE}" && -n "${READSB_DEVICE_INDEX:-}" ]]; then
  READSB_DEVICE="${READSB_DEVICE_INDEX}"
fi
if [[ -z "${READSB_DEVICE}" && -n "${RTL_DEVICE_INDEX:-}" ]]; then
  READSB_DEVICE="${RTL_DEVICE_INDEX}"
fi
READSB_GAIN="${READSB_GAIN:-49.6}"
READSB_FREQ="${READSB_FREQ:-1090000000}"
READSB_BO_PORT="${READSB_BO_PORT:-30105}"
READSB_API_PORT="${READSB_API_PORT:-8080}"

echo "Starting readsb and mlat-client (Option A: readsb inside container)"
echo "MLAT server: $MLAT_SERVER | User: $MLAT_USER"
if [[ -n "$READSB_DEVICE" ]]; then
  echo "SDR: type=$READSB_DEVICE_TYPE device=$READSB_DEVICE"
else
  echo "SDR: type=$READSB_DEVICE_TYPE device=<default>"
fi
echo "Position: lat=$LATITUDE lon=$LONGITUDE alt=$ALTITUDE"

# Require RTL-SDR present in container
if ! lsusb 2>/dev/null | grep -qiE "(Realtek.*RTL|0bda:2838|RTL2832)"; then
  echo "ERROR: No RTL-SDR USB device detected inside container."
  echo "Hints:"
  echo " - Ensure the stick is connected and not in use on the host (stop other SDR apps)."
  echo " - Compose should have: devices: - /dev/bus/usb:/dev/bus/usb and privileged: true."
  echo " - Run 'lsusb' on host to verify the device is present."
  exit 1
fi

# Start readsb on RTL-SDR
# Build optional --device flag if provided (supports index or serial)
READSB_DEVICE_FLAG=()
if [[ -n "$READSB_DEVICE" ]]; then
  READSB_DEVICE_FLAG=(--device="$READSB_DEVICE")
fi

#Debug log
echo "Position: lat=$LATITUDE lon=$LONGITUDE alt=$ALTITUDE"

# Ensure mlatuser can write lighttpd logs
mkdir -p /var/log/lighttpd
chown -R mlatuser:mlatuser /var/log/lighttpd

# Ensure mlatuser can write lighttpd logs
#set user permissions
chown -R mlatuser:mlatuser /app || true

chown -R mlatuser:dialout /dev/bus/usb || true
chown -R mlatuser:dialout /dev/rtlsdr || true
mkdir -p /run/readsb

chown -R mlatuser:mlatuser /run/readsb || true
chmod -R a+rwX /run/readsb || true

gosu mlatuser readsb \
  --device-type "$READSB_DEVICE_TYPE" \
  ${READSB_DEVICE_FLAG[@]:-} \
  --net \
  --gain="$READSB_GAIN" \
  --freq="$READSB_FREQ" \
  --lat="$LATITUDE" \
  --lon="$LONGITUDE" \
  --net-bo-port="$READSB_BO_PORT" \
  --modeac \
  --write-json=/run/readsb \
  --write-json-every=10 \
  --heatmap-dir=/data \
  --heatmap=300 \
  > /tmp/readsb.log 2>&1 &
READSB_PID=$!

# Wait for Beast-output port to be ready
echo "Waiting for readsb Beast output on port $READSB_BO_PORT ..."
for i in {1..30}; do
  if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', int('$READSB_BO_PORT'))); s.close()" 2>/dev/null; then
    echo "Port $READSB_BO_PORT is ready (after $i checks)"
    # Sanity: give readsb a moment and ensure it stays alive
    sleep 1
    if ! kill -0 "$READSB_PID" 2>/dev/null; then
      echo "ERROR: readsb died right after opening the port. Last log:"
      sed -n '1,200p' /tmp/readsb.log || true
      exit 1
    fi
    break
  fi
  sleep 1
  if ! kill -0 "$READSB_PID" 2>/dev/null; then
  echo "ERROR: readsb exited unexpectedly. Last log:"
    sed -n '1,200p' /tmp/readsb.log || true
    exit 1
  fi
done

# Start mlat-client pointed at local Beast output
mlat-client \
  --input-type beast \
  --input-connect 127.0.0.1:"$READSB_BO_PORT" \
  --server "$MLAT_SERVER" \
  --lat "$LATITUDE" \
  --lon "$LONGITUDE" \
  --alt "$ALTITUDE" \
  --user "$MLAT_USER" \
  "$@" &
MLAT_PID=$!

#start tar1090
# Use gosu to run lighttpd as the mlatuser to avoid file permission conflicts.
gosu mlatuser /usr/sbin/lighttpd -D -f /etc/lighttpd/lighttpd.conf &
LIGHTTPD_PID=$!

# Graceful shutdown
term_handler() {
  echo "Stopping..."
  kill "$LIGHTTPD_PID" 2>/dev/null || true  # Added kill for lighttpd
  kill "$MLAT_PID" 2>/dev/null || true
  kill "$READSB_PID" 2>/dev/null || true
  wait "$LIGHTTPD_PID" 2>/dev/null || true  # Added wait for lighttpd
  wait "$MLAT_PID" 2>/dev/null || true
  wait "$READSB_PID" 2>/dev/null || true
}
trap term_handler SIGTERM SIGINT

# Wait for all processes
wait "$READSB_PID" "$MLAT_PID" "$LIGHTTPD_PID"
