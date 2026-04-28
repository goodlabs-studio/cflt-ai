# tools package
# Expose hyphen-named modules under underscore aliases for importability
import importlib
import sys
from pathlib import Path

_tools_dir = Path(__file__).parent

def _load_hyphenated(name: str):
    """Load a module with hyphens in its filename via importlib."""
    spec = importlib.util.spec_from_file_location(
        f"tools.{name.replace('-', '_')}",
        _tools_dir / f"{name}.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"tools.{name.replace('-', '_')}"] = mod
    spec.loader.exec_module(mod)
    return mod

# Pre-register so `from tools.review_to_docx import ...` works
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location(
    "tools.review_to_docx",
    _tools_dir / "review-to-docx.py",
)
_mod = _ilu.module_from_spec(_spec)
sys.modules["tools.review_to_docx"] = _mod
_spec.loader.exec_module(_mod)
