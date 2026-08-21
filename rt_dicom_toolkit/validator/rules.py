"""
DICOM anonymization validation rules.
"""

class ValidationRules:
    """Define the DICOM anonymization validation rules."""
    
    def __init__(self):
        """Initialize validation rules."""
        self.define_validation_rules()
    
    def define_validation_rules(self):
        """Populate tag groups used by the validator."""
        # Attributes that must be anonymized.
        self.must_anonymize_tags = [
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientAddress",
            "PatientTelephoneNumbers",
            "ReferringPhysicianName",
            "PhysiciansOfRecord",
            "PerformingPhysicianName",
            "InstitutionName",
            "InstitutionAddress",
            "StationName",
            "OperatorsName"
        ]
        
        # UID attributes.
        self.uid_tags = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID"
        ]
        
        # Attributes that should preserve data structure.
        self.structure_tags = [
            "Modality",
            "SOPClassUID",
            "ImageType",
            "SamplesPerPixel",
            "PhotometricInterpretation",
            "BitsAllocated",
            "BitsStored",
            "HighBit",
            "PixelRepresentation",
            "NumberOfFrames"
        ]
        
        # Attributes whose handling depends on the selected level.
        self.optional_anonymize_tags = [
            "StudyDate",
            "SeriesDate",
            "AcquisitionDate",
            "ContentDate",
            "StudyTime",
            "SeriesTime",
            "AcquisitionTime",
            "ContentTime",
            "AccessionNumber",
            "StudyID",
            "SeriesNumber",
            "AcquisitionNumber",
            "InstanceNumber",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "DeviceSerialNumber"
        ]
        
        # RT-specific attributes.
        self.rt_specific_tags = [
            "StructureSetLabel",
            "StructureSetName",
            "ROIName",
            "DoseComment",
            "PlanLabel"
        ]
