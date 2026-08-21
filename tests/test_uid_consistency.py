import pytest
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer
from pydicom.uid import generate_uid

@pytest.fixture
def anonymizer():
    anonymizer = RTDicomAnonymizer()
    anonymizer.uid_handling = "consistent"
    # mock log_message to avoid clutter
    anonymizer.log_message = lambda x: None
    return anonymizer

def test_uid_consistency_recursive_replacement(anonymizer):
    old_uid_1 = "1.2.3.4.5"
    old_uid_2 = "1.2.3.4.6"
    
    # Create a synthetic UID map.
    anonymizer.uid_map[old_uid_1] = generate_uid()
    anonymizer.uid_map[old_uid_2] = generate_uid()
    
    # Create a synthetic dataset.
    dcm = Dataset()
    dcm.SOPInstanceUID = old_uid_1
    
    # Reference inside a sequence.
    ref_sq = Sequence()
    ref_item = Dataset()
    ref_item.ReferencedSOPInstanceUID = old_uid_1
    ref_sq.append(ref_item)
    dcm.ReferencedSOPSequence = ref_sq
    
    # Reference inside a deeper sequence.
    deep_sq = Sequence()
    deep_item = Dataset()
    deep_item.ReferencedSOPInstanceUID = old_uid_2
    deep_sq.append(deep_item)
    dcm.ReferencedStudySequence = deep_sq
    
    # Replace mapped UID references.
    replaced_count = anonymizer._replace_uid_references(dcm)
    
    assert replaced_count == 3  # SOPInstanceUID(1) + RefSOP(1) + DeepSOP(1)
    assert dcm.SOPInstanceUID == anonymizer.uid_map[old_uid_1]
    assert dcm.ReferencedSOPSequence[0].ReferencedSOPInstanceUID == anonymizer.uid_map[old_uid_1]
    assert dcm.ReferencedStudySequence[0].ReferencedSOPInstanceUID == anonymizer.uid_map[old_uid_2]

def test_profiles_uid_lambda():
    anonymizer = RTDicomAnonymizer()
    anonymizer.uid_handling = "consistent"
    profile = anonymizer.get_modified_anonymization_profile()
    
    old_uid = "1.1.1.1"
    # Calling the profile function registers the mapping.
    new_uid = profile["SOPInstanceUID"](old_uid)
    
    assert old_uid in anonymizer.uid_map
    assert anonymizer.uid_map[old_uid] == new_uid
    
    # The same old UID returns the same new UID.
    new_uid_2 = profile["SOPInstanceUID"](old_uid)
    assert new_uid_2 == new_uid
