#!/usr/bin/env bash
# =============================================================================
# image-arch-gate.sh — assert every pinned image publishes an s390x manifest
# =============================================================================
# The single biggest source of friction on this build. A missing s390x manifest
# does not fail at `helm install`; it fails at pod scheduling, hours later, as an
# opaque ImagePullBackOff or (worse) an exec-format error inside a running pod.
#
# NOTE: passing this gate is NECESSARY BUT NOT SUFFICIENT for connectors.
# Confluent's s390x support explicitly excludes "connectors that rely on native
# OS libraries" — a connector can ship a valid s390x manifest and still shell out
# to an x86-only native lib at runtime. Screen connectors individually.
#
#   ./image-arch-gate.sh images.txt
#
# images.txt: one fully-qualified, TAG-PINNED image per line. No `latest`.
# =============================================================================
set -euo pipefail

REQUIRED_ARCH="s390x"
IMAGES_FILE="${1:-images.txt}"

if [[ ! -f "${IMAGES_FILE}" ]]; then
  echo "usage: $0 <images.txt>" >&2
  exit 2
fi

fail=0
while IFS= read -r image; do
  # Skip blanks and comments
  [[ -z "${image}" || "${image}" =~ ^[[:space:]]*# ]] && continue

  if [[ "${image}" == *:latest || "${image}" != *:* ]]; then
    echo "[FAIL] ${image} — must be tag-pinned (never :latest on a mixed-arch registry)"
    fail=1
    continue
  fi

  if ! manifest=$(docker manifest inspect "${image}" 2>/dev/null); then
    echo "[FAIL] ${image} — manifest not readable (auth? typo? not published?)"
    fail=1
    continue
  fi

  if grep -q "\"architecture\": \"${REQUIRED_ARCH}\"" <<<"${manifest}"; then
    echo "[ ok ] ${image}"
  else
    arches=$(grep -o '"architecture": "[^"]*"' <<<"${manifest}" \
             | sed 's/.*: "//;s/"//' | sort -u | tr '\n' ' ')
    echo "[FAIL] ${image} — no ${REQUIRED_ARCH} manifest (has: ${arches:-none})"
    fail=1
  fi
done <"${IMAGES_FILE}"

if (( fail )); then
  echo
  echo "One or more images lack an ${REQUIRED_ARCH} manifest. Do not deploy."
  exit 1
fi

echo
echo "All images publish ${REQUIRED_ARCH} manifests."
