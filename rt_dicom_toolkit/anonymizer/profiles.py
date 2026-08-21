"""
DICOM anonymization profiles.
"""

import hashlib
from pydicom.uid import generate_uid

def get_anonymization_profile(anonymizer):
    """
    Return the anonymization profile.
    
    Args:
        anonymizer: Active RTDicomAnonymizer instance.
        
    Returns:
        Mapping of DICOM keywords to replacement values or callables.
    """
    # Keys are DICOM keywords; values are replacements or callables.
    return {
        # Basic patient information.
        "PatientName": "ANONYMOUS",
        "PatientID": lambda x: anonymizer.generate_anonymous_id(x),
        "PatientBirthDate": "19000101",
        "PatientSex": "O",  # Other
        "PatientAge": "000Y",
        "PatientWeight": "",
        "PatientAddress": "",
        "PatientTelephoneNumbers": "",
        
        # Study and institution information.
        "StudyID": lambda x: hashlib.md5(str(x).encode()).hexdigest()[:8],
        "AccessionNumber": "",
        "InstitutionName": "ANONYMOUS_INSTITUTION",
        "InstitutionAddress": "",
        "ReferringPhysicianName": "ANONYMOUS_PHYSICIAN",
        "PhysiciansOfRecord": "",
        "PerformingPhysicianName": "",
        "OperatorsName": "",
        
        # Identifiers.
        "StudyInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
        "SeriesInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
        "SOPInstanceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
        "FrameOfReferenceUID": lambda x: anonymizer.uid_map.setdefault(str(x), generate_uid()),
        
        # Dates and times used by the full profile.
        "StudyDate": "20000101",
        "SeriesDate": "20000101",
        "AcquisitionDate": "20000101",
        "ContentDate": "20000101",
        "StudyTime": "000000.000",
        "SeriesTime": "000000.000",
        "AcquisitionTime": "000000.000",
        "ContentTime": "000000.000",
        
        # Other identifying information.
        "DeviceSerialNumber": "",
        "StationName": "ANON_STATION",
        "ManufacturerModelName": "",
        
        # RT-specific attributes.
        "StructureSetLabel": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
        "StructureSetName": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
        "ROIName": lambda x: f"ROI_{str(x)[-10:]}" if not any(organ in str(x).lower() for organ in ["lung", "heart", "liver", "kidney", "spinal", "brain"]) else str(x),
        "DoseComment": "ANONYMIZED",
        "PlanLabel": lambda x: f"ANONYMOUS_PLAN_{str(x)[-5:]}",
    }
