"""
File and directory utilities.
"""

import os
import pydicom
import numpy as np
from pathlib import Path

def find_dicom_files(directory):
    """
    Recursively find readable DICOM files.
    
    Args:
        directory: Directory to search.
        
    Returns:
        List of DICOM file paths.
    """
    dicom_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            
            # Skip known non-DICOM extensions.
            if file_path.suffix.lower() in ['.lnk', '.ini', '.txt', '.log']:
                continue
                
            try:
                # Check whether pydicom can read the file.
                dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                
                # Accept files that contain other common DICOM attributes even
                # when SOPClassUID is absent.
                is_dicom = False
                
                # SOP Class UID is the strongest signal.
                if hasattr(dcm, 'SOPClassUID'):
                    is_dicom = True
                # Modality is also a useful signal.
                elif hasattr(dcm, 'Modality'):
                    is_dicom = True
                # Patient ID is accepted for legacy non-standard input.
                elif hasattr(dcm, 'PatientID'):
                    is_dicom = True
                # Fall back to a minimum number of DICOM data elements.
                elif len(dcm) >= 5:
                    is_dicom = True
                
                if is_dicom:
                    dicom_files.append(file_path)
            except Exception as e:
                # A caller may add focused diagnostics when required.
                pass
    
    return dicom_files

def get_relative_path(file_path, base_dir):
    """
    Return a path relative to a base directory when possible.
    
    Args:
        file_path: File path.
        base_dir: Base directory.
        
    Returns:
        Relative path, or the file name when it is outside the base.
    """
    file_path = Path(file_path)
    base_dir = Path(base_dir)
    
    try:
        return file_path.relative_to(base_dir)
    except ValueError:
        return file_path.name

def ensure_directory_exists(directory_path):
    """
    Create a directory when it does not exist.
    
    Args:
        directory_path: Directory path to create.
        
    Returns:
        Created or existing Path object.
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def copy_directory_structure(src_dir, dst_dir):
    """
    Copy a directory tree without copying files.
    
    Args:
        src_dir: Source directory.
        dst_dir: Destination directory.
        
    Returns:
        Number of created directories.
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    
    # Create the destination root.
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    # Recreate subdirectories recursively.
    created_dirs = 0
    for root, dirs, _ in os.walk(src_dir):
        for dir_name in dirs:
            src_subdir = Path(root) / dir_name
            rel_path = get_relative_path(src_subdir, src_dir)
            dst_subdir = dst_dir / rel_path
            
            dst_subdir.mkdir(exist_ok=True)
            created_dirs += 1
    
    return created_dirs

def compare_directory_structure(original_dir, anonymized_dir, log_func=print):
    """
    Compare two directory trees and return a summary.
    
    Args:
        original_dir: Original directory.
        anonymized_dir: Anonymized directory.
        log_func: Function used for progress messages.
        
    Returns:
        Dictionary containing comparison results.
    """
    original_dir = Path(original_dir)
    anonymized_dir = Path(anonymized_dir)
    
    if not original_dir.exists() or not anonymized_dir.exists():
        log_func("One or both specified directories do not exist.")
        return {"summary": ["One or both specified directories do not exist."]}
    
    # Count DICOM files.
    original_files = find_dicom_files(original_dir)
    anonymized_files = find_dicom_files(anonymized_dir)
    
    log_func(f"DICOM files in original directory: {len(original_files)}")
    log_func(f"DICOM files in anonymized directory: {len(anonymized_files)}")
    
    # Build the summary.
    summary = []
    summary.append("=== Directory comparison ===")
    summary.append(f"Original directory: {original_dir}")
    summary.append(f"Anonymized directory: {anonymized_dir}")
    summary.append(f"Original DICOM files: {len(original_files)}")
    summary.append(f"Anonymized DICOM files: {len(anonymized_files)}")
    
    if len(original_files) == len(anonymized_files):
        summary.append("\n✅ File counts match.")
    else:
        summary.append("\n⚠️ File counts do not match.")
        if len(original_files) > len(anonymized_files):
            summary.append(f"  Missing files: {len(original_files) - len(anonymized_files)}")
        else:
            summary.append(f"  Extra files: {len(anonymized_files) - len(original_files)}")
    
    # Collect Modality distributions.
    original_modalities = {}
    anonymized_modalities = {}
    
    for file_path in original_files:
        try:
            dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
            if hasattr(dcm, 'Modality'):
                modality = dcm.Modality
                if modality in original_modalities:
                    original_modalities[modality] += 1
                else:
                    original_modalities[modality] = 1
        except:
            pass
    
    for file_path in anonymized_files:
        try:
            dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
            if hasattr(dcm, 'Modality'):
                modality = dcm.Modality
                if modality in anonymized_modalities:
                    anonymized_modalities[modality] += 1
                else:
                    anonymized_modalities[modality] = 1
        except:
            pass
    
    # Add Modality distributions to the summary.
    summary.append("\n=== Modality distribution ===")
    modalities = list(set(list(original_modalities.keys()) + list(anonymized_modalities.keys())))
    original_counts = [original_modalities.get(m, 0) for m in modalities]
    anonymized_counts = [anonymized_modalities.get(m, 0) for m in modalities]
    
    for modality in modalities:
        orig_count = original_modalities.get(modality, 0)
        anon_count = anonymized_modalities.get(modality, 0)
        status = "✅" if orig_count == anon_count else "⚠️"
        summary.append(f"{status} {modality}: original {orig_count}, anonymized {anon_count}")
    
    return {
        "summary": summary,
        "original_files": len(original_files),
        "anonymized_files": len(anonymized_files),
        "modality_data": {
            "modalities": modalities,
            "original_counts": original_counts,
            "anonymized_counts": anonymized_counts
        }
    }
