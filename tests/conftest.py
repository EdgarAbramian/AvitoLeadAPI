import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
