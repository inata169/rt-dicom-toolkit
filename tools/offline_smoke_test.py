#!/usr/bin/env python3
"""Run an end-to-end smoke test using only synthetic non-patient DICOM data."""

from __future__ import annotations

import os
from pathlib import Path
import struct
import tempfile


def _create_ct(path: Path, *, patient_name: str, patient_id: str) -> None:
    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

    sop_instance_uid = generate_uid()
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    dataset = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False
    dataset.SOPClassUID = CTImageStorage
    dataset.SOPInstanceUID = sop_instance_uid
    dataset.StudyInstanceUID = generate_uid()
    dataset.SeriesInstanceUID = generate_uid()
    dataset.FrameOfReferenceUID = generate_uid()
    dataset.Modality = "CT"
    dataset.PatientName = patient_name
    dataset.PatientID = patient_id
    dataset.PatientBirthDate = "19000101"
    dataset.PatientSex = "O"
    dataset.StudyID = "SYNTHETIC"
    dataset.StudyDate = "20000101"
    dataset.StudyTime = "120000"
    dataset.AccessionNumber = "SYNTHETIC"
    dataset.ImagePositionPatient = [0.0, 0.0, 0.0]
    dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    dataset.PixelSpacing = [1.0, 1.0]
    dataset.SliceThickness = 1.0
    dataset.Rows = 2
    dataset.Columns = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelData = struct.pack("<4H", 0, 100, 200, 300)
    private_block = dataset.private_block(0x0029, "SYNTHETIC CREATOR", create=True)
    private_block.add_new(0x01, "LO", "SYNTHETIC PRIVATE VALUE")
    dataset.save_as(str(path), write_like_original=False)


def run_smoke_test() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")

    import tkinter  # noqa: F401
    import customtkinter  # noqa: F401
    from matplotlib.backends import backend_tkagg  # noqa: F401
    import pydicom

    from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer
    from rt_dicom_toolkit.template import DICOMTemplateEngine
    from rt_dicom_toolkit.validator.core import RTDicomValidator

    with tempfile.TemporaryDirectory(prefix="rt-dicom-toolkit-smoke-") as temp_name:
        root = Path(temp_name)
        original_dir = root / "original"
        anonymized_dir = root / "anonymized"
        log_dir = root / "logs"
        report_dir = root / "reports"
        original_dir.mkdir()
        report_dir.mkdir()

        original_path = original_dir / "synthetic_ct.dcm"
        _create_ct(
            original_path,
            patient_name="SYNTHETIC^NONPATIENT",
            patient_id="SYNTHETIC001",
        )

        original = pydicom.dcmread(str(original_path), force=False)
        original_sop_uid = str(original.SOPInstanceUID)
        original_pixels = bytes(original.PixelData)
        if not any(tag.is_private for tag in original.keys()):
            raise AssertionError("Synthetic input does not contain the expected private tag")

        anonymizer = RTDicomAnonymizer()
        anonymizer.input_dir = original_dir
        anonymizer.output_dir = anonymized_dir
        anonymizer.log_dir = log_dir
        anonymizer.private_tags = "remove"
        anonymizer.uid_handling = "consistent"
        anonymizer.process_directory()

        anonymized_path = anonymized_dir / original_path.name
        if not anonymized_path.is_file():
            raise AssertionError("Anonymizer did not create the output DICOM")
        anonymized = pydicom.dcmread(str(anonymized_path), force=False)
        if str(anonymized.PatientName) != "ANONYMOUS":
            raise AssertionError("PatientName was not anonymized")
        if str(anonymized.PatientID) == "SYNTHETIC001":
            raise AssertionError("PatientID was not anonymized")
        if str(anonymized.SOPInstanceUID) == original_sop_uid:
            raise AssertionError("SOPInstanceUID was not replaced")
        if any(tag.is_private for tag in anonymized.keys()):
            raise AssertionError("Private tags were not removed")
        if bytes(anonymized.PixelData) != original_pixels:
            raise AssertionError("PixelData changed during anonymization")

        validator = RTDicomValidator()
        validator.report_dir = report_dir
        comparison = validator.compare_dicom_files(original_path, anonymized_path)
        if not comparison:
            raise AssertionError("Validator did not return comparison results")
        if not comparison["must_anonymize"]["PatientName"]["anonymized"]:
            raise AssertionError("Validator did not detect PatientName anonymization")
        if comparison["private_tags"]["anonymized_count"] != 0:
            raise AssertionError("Validator detected a remaining private tag")
        if not comparison["pixel_data"]["match"]:
            raise AssertionError("Validator did not confirm PixelData preservation")
        report = validator.validate_files(original_dir, anonymized_dir)
        if not report:
            raise AssertionError("Directory validation did not produce a report")

        template_path = root / "synthetic_template.dcm"
        _create_ct(
            template_path,
            patient_name="TEMPLATE^NONPATIENT",
            patient_id="TEMPLATE001",
        )
        template_engine = DICOMTemplateEngine(str(template_path))
        synchronized = template_engine.sync_from_source(str(original_path))
        if str(synchronized.PatientID) != "SYNTHETIC001":
            raise AssertionError("Template engine did not synchronize PatientID")
        if list(synchronized.PixelSpacing) != [1.0, 1.0]:
            raise AssertionError("Template engine did not synchronize geometry")
        if str(synchronized.SOPInstanceUID) == str(
            template_engine._template_dcm.SOPInstanceUID
        ):
            raise AssertionError("Template engine did not generate a new SOP UID")


def main() -> int:
    try:
        run_smoke_test()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("SMOKE TEST PASSED: anonymizer, validator, template engine, and GUI imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
