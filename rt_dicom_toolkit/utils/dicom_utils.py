"""
DICOM utility functions.
"""

import pydicom
import os
from pathlib import Path

def get_dicom_info(file_path):
    """
    Return basic information for a DICOM file.
    
    Args:
        file_path: Path to the DICOM file.
        
    Returns:
        A dictionary of basic attributes, or None when reading fails.
    """
    try:
        dcm = pydicom.dcmread(str(file_path), force=True)
        
        # Extract basic attributes.
        info = {}
        for tag in ['Modality', 'PatientID', 'PatientName', 'StudyDate', 'SeriesDescription']:
            if hasattr(dcm, tag):
                info[tag] = getattr(dcm, tag)
            else:
                info[tag] = None
        
        # Add file-path information.
        info['FilePath'] = str(file_path)
        info['FileName'] = Path(file_path).name
        
        return info
    except Exception:
        return None

def is_dicom_file(file_path):
    """
    Return whether a file can be read as standard DICOM.
    
    Args:
        file_path: Path to inspect.
        
    Returns:
        True for readable DICOM; otherwise False.
    """
    try:
        pydicom.dcmread(str(file_path), force=False, stop_before_pixels=True)
        return True
    except Exception:
        return False

def get_dicom_modality(file_path):
    """
    Return the DICOM Modality value.
    
    Args:
        file_path: Path to the DICOM file.
        
    Returns:
        Modality string, or 'Unknown' when unavailable.
    """
    try:
        dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
        if hasattr(dcm, 'Modality'):
            return dcm.Modality
        return 'Unknown'
    except Exception:
        return 'Unknown'

def get_dicom_description(file_path):
    """
    Return a general description based on Modality.
    
    Args:
        file_path: Path to the DICOM file.
        
    Returns:
        Human-readable file-type description.
    """
    modality = get_dicom_modality(file_path)
    
    if modality == 'RTPLAN':
        return 'Radiotherapy plan'
    elif modality == 'RTDOSE':
        return 'Dose distribution'
    elif modality == 'RTSTRUCT':
        return 'Structure contours'
    elif modality == 'CT':
        return 'CT image'
    elif modality == 'RTIMAGE':
        return 'Treatment image'
    elif modality == 'MR':
        return 'MR image'
    else:
        return f'{modality} file'
