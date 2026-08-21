import os
import pytest
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from rt_dicom_toolkit.template import DICOMTemplateEngine

@pytest.fixture
def mock_dicom_files(tmp_path):
    """Create synthetic DICOM files for template tests."""
    # Template file.
    template_path = tmp_path / "template.dcm"
    template_dcm = FileDataset(str(template_path), {}, file_meta=FileMetaDataset())
    template_dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    template_dcm.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.2" # RT DOSE
    template_dcm.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    template_dcm.is_little_endian = True
    template_dcm.is_implicit_VR = False
    
    template_dcm.Modality = "RTDOSE"
    template_dcm.PatientName = "TEMPLATE^PATIENT"
    template_dcm.PatientID = "TMPL001"
    template_dcm.ImagePositionPatient = [0, 0, 0]
    template_dcm.PixelSpacing = [1.0, 1.0]
    template_dcm.SOPInstanceUID = template_dcm.file_meta.MediaStorageSOPInstanceUID
    template_dcm.save_as(str(template_path), write_like_original=False)
    
    # Source file.
    source_path = tmp_path / "source.dcm"
    source_dcm = FileDataset(str(source_path), {}, file_meta=FileMetaDataset())
    source_dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    source_dcm.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.2"
    source_dcm.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    source_dcm.is_little_endian = True
    source_dcm.is_implicit_VR = False
    
    source_dcm.Modality = "RTDOSE"
    source_dcm.PatientName = "SOURCE^NONPATIENT"
    source_dcm.PatientID = "SOURCE123"
    source_dcm.ImagePositionPatient = [-100.5, -50.0, 25.5]
    source_dcm.PixelSpacing = [2.5, 2.5]
    source_dcm.SOPInstanceUID = source_dcm.file_meta.MediaStorageSOPInstanceUID
    source_dcm.save_as(str(source_path), write_like_original=False)
    
    return str(template_path), str(source_path)

def test_template_engine_init(mock_dicom_files):
    template_path, _ = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    assert engine.template_path == template_path
    assert engine._template_dcm.PatientID == "TMPL001"

def test_sync_from_source(mock_dicom_files):
    template_path, source_path = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    # Synchronize all configured groups.
    synced_dcm = engine.sync_from_source(source_path)
    
    # Patient attributes come from the source.
    assert synced_dcm.PatientName == "SOURCE^NONPATIENT"
    assert synced_dcm.PatientID == "SOURCE123"
    
    # Geometry comes from the source.
    assert synced_dcm.ImagePositionPatient == [-100.5, -50.0, 25.5]
    assert synced_dcm.PixelSpacing == [2.5, 2.5]
    
    # New UIDs are generated.
    assert synced_dcm.SOPInstanceUID != engine._template_dcm.SOPInstanceUID
    assert synced_dcm.file_meta.MediaStorageSOPInstanceUID == synced_dcm.SOPInstanceUID
    
def test_sync_partial(mock_dicom_files):
    template_path, source_path = mock_dicom_files
    engine = DICOMTemplateEngine(template_path)
    
    # Synchronize geometry only.
    synced_dcm = engine.sync_from_source(source_path, sync_patient=False)
    
    # Patient attributes remain from the template.
    assert synced_dcm.PatientID == "TMPL001"
    
    # Geometry comes from the source.
    assert synced_dcm.PixelSpacing == [2.5, 2.5]
