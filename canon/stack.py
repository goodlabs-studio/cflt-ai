#!/usr/bin/env python3
"""
canon/stack.py — Canon overlay stack resolution.

Loads base defaults, then merges industry/customer/engagement overrides
in order. Computes a SHA-256 hash of the resolved config for provenance.

Usage:
    from canon.stack import resolve_stack
    config, stack_hash = resolve_stack()
    # config is the merged dict, stack_hash is a hex string

H.4b: resolve_stack() now accepts `family` and `canon_layer` keyword args.
      Operator family (default) uses industry/fsi as before; developer family
      routes to the profile's canon_layer (default industry/fsi/developer-sandbox).
      v1.0 callers (resolve_stack() with no args, or with customer=...) are
      byte-compatible — the operator default preserves exact pre-H.4b behavior.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


CANON_ROOT = Path(__file__).resolve().parent


def _layer_order_for(family: str = "operator", canon_layer: Optional[str] = None) -> List[str]:
    """Compute the layer order for the canon stack (H.4b).

    Operator family uses the prod FSI overlay (industry/fsi) as the industry layer.
    Developer family uses `canon_layer` (defaults to industry/fsi/developer-sandbox)
    as the industry layer.

    Customer and engagement layers are appended last regardless of family.

    Args:
        family:      "operator" (default) or "developer".
        canon_layer: Optional explicit industry-layer path. When None, defaults are
                     operator → "industry/fsi"; developer → "industry/fsi/developer-sandbox".

    Returns:
        List of layer names in composition order.

    Raises:
        ValueError: If family is not a recognized canon family.
    """
    if family == "developer":
        industry_layer = canon_layer or "industry/fsi/developer-sandbox"
    elif family == "operator":
        industry_layer = canon_layer or "industry/fsi"
    else:
        raise ValueError(f"Unknown profile family for canon stack: {family!r}")
    return ["base", industry_layer, "customer", "engagement"]


# Module-level constant for back-compat — any code that imported LAYER_ORDER directly
# still gets the operator-family default order. H.4b: prefer _layer_order_for() in new code.
LAYER_ORDER = _layer_order_for()


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
    family: str = "operator",
    canon_layer: Optional[str] = None,
) -> Tuple[Dict, str]:
    """Resolve the full canon stack by merging layers in order.

    Args:
        layers:      Override default layer order (for testing). When provided,
                     `family` and `canon_layer` are ignored — caller has full control.
        customer:    Customer name to load customer/{name}/overrides.yaml.
        engagement:  Engagement name to load engagement/{name}/overrides.yaml.
        family:      "operator" (default) or "developer" — selects industry-layer
                     routing when `layers` is not explicitly provided. Default
                     preserves byte-identical v1.0 behavior.
        canon_layer: Optional explicit industry-layer path (e.g.,
                     "industry/fsi/developer-sandbox"). Used when the profile JSON
                     specifies its own canon_layer field. If None, defaults are
                     operator → "industry/fsi"; developer → "industry/fsi/developer-sandbox".

    Returns:
        Tuple of (merged_config_dict, sha256_hex_hash).

    Raises:
        ValueError: If family is unknown (via _layer_order_for).
    """
    if layers is None:
        layers = _layer_order_for(family=family, canon_layer=canon_layer)

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
