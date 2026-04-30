"""
DICOMテンプレート同期に使用するタグ定義
"""

# 患者・検査情報（基本的な識別子）
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

# 幾何学的・画像情報（座標や解像度）
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

# RTDOSEなどに特有のタグ（必要に応じて同期）
RT_SPECIFIC_TAGS = [
    "GridFrameOffsetVector",
    "DoseGridScaling",
    "DoseSummationType",
    "DoseType",
    "DoseUnits",
]
