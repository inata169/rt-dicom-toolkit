"""
Utilities for anonymization.
"""

import hashlib
import uuid
from pydicom.uid import generate_uid

def generate_uid_from_string(input_str):
    """
    Generate a deterministic UID from a string.
    
    Args:
        input_str: Input value.
        
    Returns:
        DICOM-formatted UID.
    """
    # Hash the input string.
    hash_obj = hashlib.md5(str(input_str).encode())
    hash_hex = hash_obj.hexdigest()
    
    # Use the UUID-derived 2.25 UID root.
    uid = "2.25." + str(int(hash_hex, 16) % 10**38)
    
    return uid[:64]  # A DICOM UID is limited to 64 characters.

def generate_anonymous_patient_id(original_id, prefix="ANO", method="hash"):
    """
    Generate an anonymized patient ID.
    
    Args:
        original_id: Original patient ID.
        prefix: Anonymized-ID prefix.
        method: Either 'hash' or 'uuid'.
        
    Returns:
        Anonymized patient ID.
    """
    if method == "hash":
        # Generate a short deterministic value from the MD5 digest.
        hash_obj = hashlib.md5(str(original_id).encode())
        hash_hex = hash_obj.hexdigest()
        return f"{prefix}{hash_hex[:8]}"
    elif method == "uuid":
        # Use part of a newly generated UUID.
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        return f"{prefix}{short_uuid}"
    else:
        raise ValueError(f"Unknown generation method: {method}")
