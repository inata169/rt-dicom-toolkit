#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run the anonymization workflow.
"""

from pathlib import Path
import sys
import os

# Add the repository package to the import path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer
from rt_dicom_toolkit.config import DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_LOG_DIR

def main():
    """Run anonymization with the configured default directories."""
    print("Starting anonymization...")
    
    # Create the anonymizer.
    anonymizer = RTDicomAnonymizer()
    
    # Display the active directories.
    print(f"Input directory: {anonymizer.input_dir}")
    print(f"Output directory: {anonymizer.output_dir}")
    print(f"Log directory: {anonymizer.log_dir}")
    
    # Run anonymization.
    anonymizer.process_directory()
    
    print("Anonymization completed.")

if __name__ == "__main__":
    main()
