"""
DICOM keywords used by template synchronization.
"""

# Patient and study identifiers.
PATIENT_TAGS = [
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "StudyInstanceUID",
    "StudyID",
    "StudyDate",
    "StudyTime",
    "AccessionNumber",
]

# Geometry and image attributes.
GEOMETRY_TAGS = [
    "ImagePositionPatient",
    "ImageOrientationPatient",
    "PixelSpacing",
    "SliceThickness",
    "Rows",
    "Columns",
    "FrameOfReferenceUID",
    "PositionReferenceIndicator",
    "NumberOfFrames",
]

# RT-specific attributes, including RTDOSE values.
RT_SPECIFIC_TAGS = [
    "GridFrameOffsetVector",
    "DoseGridScaling",
    "DoseSummationType",
    "DoseType",
    "DoseUnits",
]
