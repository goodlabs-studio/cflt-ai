import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def wiki_root(project_root):
    """Return the wiki directory."""
    return project_root / "wiki"


@pytest.fixture
def tools_dir(project_root):
    """Return the tools directory."""
    return project_root / "tools"


@pytest.fixture
def fsi_dsp_root(project_root):
    """Return the fsi-dsp submodule root."""
    return project_root / "raw" / "repos" / "fsi-dsp"
