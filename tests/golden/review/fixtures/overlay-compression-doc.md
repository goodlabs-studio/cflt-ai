# Producer Compression Configuration Guide

## Overview

This document provides guidance on selecting the appropriate compression algorithm
for Kafka producers in our streaming platform.

## Recommended Algorithm: lz4

We recommend `compression.type=lz4` for all producers in this platform.

lz4 provides excellent throughput characteristics:
- Compression ratio: approximately 2:1 for JSON payloads
- CPU overhead: very low (less than 5% CPU increase at peak load)
- Decompression speed: extremely fast on modern hardware

## Configuration

```properties
compression.type=lz4
batch.size=65536
linger.ms=5
```

## Comparison

| Algorithm | Compression Ratio | CPU Cost | Best For |
|-----------|-------------------|----------|----------|
| lz4       | Medium            | Low      | Throughput-optimized clusters |
| zstd      | High              | Medium   | Storage-constrained clusters |
| snappy    | Medium            | Low      | Legacy compatibility |
| gzip      | High              | High     | Maximum compression, CPU available |

## Conclusion

For the current cluster topology (throughput-optimized, cost-effective storage),
`lz4` is the right choice. Switch to `zstd` only if storage costs become a constraint.
