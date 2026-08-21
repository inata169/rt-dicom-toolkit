import pytest
import shutil
import pydicom
from pathlib import Path
from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer


def test_integration_anonymize(dicom_test_dir, temp_output_dir):
    """Run the focused single-file anonymization integration test."""
    source_file = dicom_test_dir / "RTPLAN_PHITStest.dcm"

    if not source_file.exists():
        pytest.skip(f"Test file {source_file} not found")

    # Copy one fixture into the temporary input directory.
    input_dir = temp_output_dir / "input"
    input_dir.mkdir()
    shutil.copy2(source_file, input_dir / source_file.name)

    output_dir = temp_output_dir / "output"
    log_dir = temp_output_dir / "logs"

    anonymizer = RTDicomAnonymizer()
    anonymizer.input_dir = input_dir
    anonymizer.output_dir = output_dir
    anonymizer.log_dir = log_dir

    anonymizer.process_directory()

    # Confirm output was created.
    output_file = output_dir / source_file.name
    assert output_file.exists(), f"Output file not found at {output_file}"

    # Use force=True to support the historical non-standard fixture. Output
    # saved with write_like_original=False should also be standard-readable.
    dcm = pydicom.dcmread(str(output_file), force=False)

    # Confirm configured values were anonymized.
    assert str(dcm.PatientName) == "ANONYMOUS", f"PatientName not anonymized: {dcm.PatientName}"
    assert hasattr(dcm, 'PatientID'), "PatientID missing"
    assert len(str(dcm.StationName)) <= 16 if hasattr(dcm, 'StationName') else True

    # Confirm standard file-meta information was added.
    assert hasattr(dcm, 'file_meta'), "file_meta missing - DICOM header not written"
    assert hasattr(dcm.file_meta, 'TransferSyntaxUID'), "TransferSyntaxUID missing in file_meta"


def test_uid_consistency(dicom_test_dir, temp_output_dir):
    """Test consistent UID handling."""
    source_file = dicom_test_dir / "RTPLAN_PHITStest.dcm"
    if not source_file.exists():
        pytest.skip(f"Test file {source_file} not found")

    input_dir = temp_output_dir / "input"
    input_dir.mkdir()
    shutil.copy2(source_file, input_dir / source_file.name)

    anonymizer = RTDicomAnonymizer()
    anonymizer.uid_handling = "consistent"
    anonymizer.input_dir = input_dir
    anonymizer.output_dir = temp_output_dir / "output"
    anonymizer.log_dir = temp_output_dir / "logs"

    anonymizer.process_directory()

    # Confirm that a UID map was created.
    assert len(anonymizer.uid_map) > 0, "uid_map should be populated in consistent mode"
