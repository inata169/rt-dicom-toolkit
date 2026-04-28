import pytest
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer
from pydicom.uid import generate_uid

@pytest.fixture
def mock_dicom():
    dcm = Dataset()
    dcm.file_meta = FileMetaDataset()
    dcm.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    dcm.PatientName = "TEST^PATIENT"
    dcm.PatientID = "123456"
    dcm.StudyInstanceUID = generate_uid()
    dcm.SeriesInstanceUID = generate_uid()
    
    # Private tag for testing
    block = dcm.private_block(0x0029, "Test Creator", create=True)
    block.add_new(0x01, "LO", "Private Data")
    return dcm

def test_anonymize_dicom(mock_dicom):
    anonymizer = RTDicomAnonymizer()
    profile = anonymizer.get_modified_anonymization_profile()
    
    # Verify private tag exists before
    assert len([t for t in mock_dicom.keys() if t.is_private]) > 0
    
    anonymizer.anonymize_dicom(mock_dicom, profile, remove_private_tags=True)
    
    # Verify anonymization
    assert str(mock_dicom.PatientName) == "ANONYMOUS"
    assert str(mock_dicom.PatientID) != "123456"
    assert len([t for t in mock_dicom.keys() if t.is_private]) == 0
