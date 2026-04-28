#!/usr/bin/env python3
"""
canon/stack.py — Canon overlay stack resolution.

Loads base defaults, then merges industry/customer/engagement overrides
in order. Computes a SHA-256 hash of the resolved config for provenance.

Usage:
    from canon.stack import resolve_stack
    config, stack_hash = resolve_stack()
    # config is the merged dict, stack_hash is a hex string
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


CANON_ROOT = Path(__file__).resolve().parent
LAYER_ORDER = ["base", "industry/fsi", "customer", "engagement"]


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins on conflict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_layer(layer_name: str) -> dict:
    """Load a layer's YAML config. Returns empty dict if not found."""
    layer_dir = CANON_ROOT / layer_name
    # Base uses defaults.yaml; all others use overrides.yaml
    if layer_name == "base":
        config_file = layer_dir / "defaults.yaml"
    else:
        config_file = layer_dir / "overrides.yaml"

    if not config_file.exists():
        return {}

    content = config_file.read_text()
    data = yaml.safe_load(content)
    return data if isinstance(data, dict) else {}


def resolve_stack(
    layers: Optional[List[str]] = None,
    customer: Optional[str] = None,
    engagement: Optional[str] = None,
) -> Tuple[Dict, str]:
    """Resolve the full canon stack by merging layers in order.

    Args:
        layers: Override default layer order (for testing).
        customer: Customer name to load customer/{name}/overrides.yaml.
        engagement: Engagement name to load engagement/{name}/overrides.yaml.

    Returns:
        Tuple of (merged_config_dict, sha256_hex_hash).
    """
    if layers is None:
        layers = list(LAYER_ORDER)

    # Substitute customer/engagement names if provided
    resolved_layers = []
    for layer in layers:
        if layer == "customer" and customer:
            resolved_layers.append(f"customer/{customer}")
        elif layer == "engagement" and engagement:
            resolved_layers.append(f"engagement/{engagement}")
        else:
            resolved_layers.append(layer)

    merged = {}

    for layer_name in resolved_layers:
        layer_data = _load_layer(layer_name)
        if layer_data:
            merged = _deep_merge(merged, layer_data)

    # Compute deterministic hash of resolved config
    canonical_json = json.dumps(merged, sort_keys=True, default=str)
    stack_hash = hashlib.sha256(canonical_json.encode()).hexdigest()[:16]

    return merged, stack_hash


def active_layers() -> List[str]:
    """Return list of layers that have config files present."""
    present = []
    for layer in LAYER_ORDER:
        layer_dir = CANON_ROOT / layer
        config = layer_dir / ("defaults.yaml" if layer == "base" else "overrides.yaml")
        if config.exists():
            present.append(layer)
    return present


def provenance_footer() -> str:
    """Generate a provenance footer string for artifact embedding."""
    config, stack_hash = resolve_stack()
    layers = active_layers()
    return f"Canon stack: {' + '.join(layers)} | Hash: {stack_hash}"


if __name__ == "__main__":
    config, stack_hash = resolve_stack()
    layers = active_layers()
    print(f"Active layers: {', '.join(layers)}")
    print(f"Stack hash: {stack_hash}")
    print(f"Resolved keys: {list(config.keys())}")
    print(f"\nProvenance: {provenance_footer()}")
