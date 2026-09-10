#!/usr/bin/env bash
# Dry run: prints 10 sample events to stdout without producing to Kafka.
set -euo pipefail
cd "$(dirname "$0")"

docker run --rm \
  --network none \
  --hostname shadowtraffic-dryrun \
  --add-host shadowtraffic-dryrun:127.0.0.1 \
  --env-file license.env \
  --env-file .env \
  -v "$(pwd)/config/shadowtraffic-config.json:/home/config.json" \
  -v "$(pwd)/config/client.properties:/home/config/client.properties" \
  shadowtraffic/shadowtraffic:latest \
  --config /home/config.json \
  --sample 10 \
  --stdout
