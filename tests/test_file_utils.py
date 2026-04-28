import pytest
from pathlib import Path
from rt_dicom_toolkit.utils.file_utils import find_dicom_files

def test_find_dicom_files_skips_lnk(tmp_path):
    # Create fake dicom and lnk
    dcm_file = tmp_path / "test.dcm"
    lnk_file = tmp_path / "shortcut.lnk"
    
    dcm_file.write_text("fake dicom")
    lnk_file.write_text("fake lnk")
    
    files = find_dicom_files(tmp_path)
    # Both fail to parse as DICOM, but shortcut.lnk shouldn't even be attempted
    # resulting in no dicom files found.
    assert len(files) == 0
