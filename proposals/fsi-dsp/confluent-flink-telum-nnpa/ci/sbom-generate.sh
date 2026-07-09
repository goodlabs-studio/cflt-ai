#!/usr/bin/env bash
# =============================================================================
# sbom-generate.sh — CycloneDX 1.6 SBOMs, one per deployable artifact
# =============================================================================
# The SBOM is generated, not written. One artifact -> one SBOM, plus a merged
# release SBOM. §10 of the runbook.
#
#   ./sbom-generate.sh images.txt ../sbom
#
# THE MULTI-ARCH FAILURE MODE, stated plainly:
#   `syft confluentinc/cp-server:8.2.0` on an x86 CI runner silently scans the
#   amd64 manifest and produces an SBOM for binaries that will never run on this
#   cluster. Two defences, both applied below:
#     1. resolve the tag to a DIGEST first, and scan the digest
#     2. pass --platform linux/s390x explicitly
#   Doing only (1) is not enough: a digest can still point at a manifest LIST.
#
# Requires: syft, cosign, crane (or docker buildx imagetools), jq.
# =============================================================================
set -euo pipefail

IMAGES_FILE="${1:-images.txt}"
OUT_DIR="${2:-../sbom}"
PLATFORM="linux/s390x"

command -v syft >/dev/null || { echo "syft not found" >&2; exit 2; }
command -v jq   >/dev/null || { echo "jq not found" >&2; exit 2; }

mkdir -p "${OUT_DIR}/images"

echo "==> Generating per-image SBOMs (${PLATFORM})"
while IFS= read -r image; do
  [[ -z "${image}" || "${image}" =~ ^[[:space:]]*# || "${image}" =~ PLACEHOLDER ]] && continue

  # Never scan by tag. Resolve to an immutable digest first.
  if ! digest=$(crane digest --platform "${PLATFORM}" "${image}" 2>/dev/null); then
    echo "[FAIL] ${image} — cannot resolve ${PLATFORM} digest (no s390x manifest?)" >&2
    exit 1
  fi

  repo="${image%%:*}"
  safe=$(tr '/:' '__' <<<"${image}")
  ref="${repo}@${digest}"

  echo "  ${image} -> ${digest}"
  syft "${ref}" \
    --platform "${PLATFORM}" \
    -o cyclonedx-json="${OUT_DIR}/images/${safe}.cdx.json"

  # Record the digest so sbom-gate.py can reconcile BOM rows 1:1 with SBOMs.
  jq -n --arg img "${image}" --arg dig "${digest}" --arg plat "${PLATFORM}" \
    '{image:$img, digest:$dig, platform:$plat}' \
    >"${OUT_DIR}/images/${safe}.ref.json"
done <"${IMAGES_FILE}"

# ---- Flink job JAR ---------------------------------------------------------
# Build-time SBOM, not a post-hoc jar scan: a post-hoc scan misses shaded and
# relocated dependencies, which is exactly where supply-chain risk hides.
if [[ -f pom.xml ]]; then
  echo "==> Generating job-JAR SBOM via cyclonedx-maven-plugin"
  mvn -q -B org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom \
    -DoutputFormat=json -DschemaVersion=1.6
  cp target/bom.json "${OUT_DIR}/fraud-scoring-jar.cdx.json"
fi

# ---- Model artifact --------------------------------------------------------
# Nonstandard and worth doing: makes "which model build, compiled how, with what
# accelerator coverage" a queryable supply-chain fact rather than tribal
# knowledge. This is precisely what an FSI model-risk-management review asks for.
if [[ -n "${MODEL_ONNX:-}" && -n "${COVERAGE_REPORT:-}" ]]; then
  echo "==> Emitting model component SBOM"
  onnx_hash=$(sha256sum "${MODEL_ONNX}" | cut -d' ' -f1)
  cov_hash=$(python3 nnpa-coverage-gate.py "${COVERAGE_REPORT}" --print-hash)
  nnpa_pct=$(jq '[.ops[] | select(.device=="NNPA")] | length as $n
                 | ($n / ([.ops[]] | length) * 100) | floor' "${COVERAGE_REPORT}" 2>/dev/null || echo 0)

  jq -n \
    --arg onnx "${onnx_hash}" \
    --arg cov "${cov_hash}" \
    --arg zdlc "${ZDLC_DIGEST:-unknown}" \
    --arg march "${TARGET_MARCH:-z16}" \
    --arg pct "${nnpa_pct}" \
    --arg covpath "${COVERAGE_REPORT}" \
    '{
      bomFormat: "CycloneDX",
      specVersion: "1.6",
      version: 1,
      components: [{
        type: "machine-learning-model",
        "bom-ref": ("model/fraud-scoring@" + $cov),
        name: "fraud-scoring",
        version: $cov,
        hashes: [{alg: "SHA-256", content: $onnx}],
        properties: [
          {name: "zdlc.image.digest",   value: $zdlc},
          {name: "zdlc.target.march",   value: $march},
          {name: "nnpa.coverage.pct",   value: $pct},
          {name: "nnpa.coverage.hash",  value: $cov}
        ],
        externalReferences: [{
          type: "attestation",
          url: $covpath,
          comment: "zDLC/onnx-mlir op-coverage report. Supply-chain twin of the Phase 4 fallback gate."
        }]
      }]
    }' >"${OUT_DIR}/model-fraud-scoring.cdx.json"
fi

# ---- Configuration layer ---------------------------------------------------
# Chart versions + values-file hashes as configuration components, so a values
# change is visible in the release SBOM.
echo "==> Hashing Helm values / Ansible as configuration components"
find ../helm ../manifests -type f \( -name '*.yaml' -o -name '*.yml' \) -print0 \
  | sort -z | xargs -0 sha256sum >"${OUT_DIR}/config-hashes.txt"

# ---- Merge -----------------------------------------------------------------
echo "==> Merging release SBOM"
if command -v cyclonedx >/dev/null; then
  # shellcheck disable=SC2046
  cyclonedx merge --output-format json \
    --input-files $(find "${OUT_DIR}" -name '*.cdx.json') \
    --output-file "${OUT_DIR}/release.cdx.json"
else
  echo "  (cyclonedx-cli not found — skipping merge; per-artifact SBOMs still emitted)"
fi

# ---- Sign ------------------------------------------------------------------
# IBM/Confluent-supplied images carry vendor signatures: record their digests and
# verification status in the BOM rather than re-signing them.
if [[ -n "${COSIGN_KEY:-}" && -n "${JOB_IMAGE:-}" ]]; then
  echo "==> Signing job image + attaching SBOM and coverage attestations"
  cosign sign --key "${COSIGN_KEY}" "${JOB_IMAGE}"
  cosign attest --key "${COSIGN_KEY}" --type cyclonedx \
    --predicate "${OUT_DIR}/release.cdx.json" "${JOB_IMAGE}"
  [[ -n "${COVERAGE_REPORT:-}" ]] && cosign attest --key "${COSIGN_KEY}" \
    --type custom --predicate "${COVERAGE_REPORT}" "${JOB_IMAGE}"
fi

echo
echo "SBOMs written to ${OUT_DIR}/"
