import pytest
from pathlib import Path

@pytest.fixture
def base_dir():
    return Path(__file__).parent.parent.absolute()

@pytest.fixture
def dicom_test_dir(base_dir):
    return base_dir / "DICOM"

@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
