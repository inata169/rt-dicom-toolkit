#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Entry point for the anonymizer package.
"""

from .core import RTDicomAnonymizer
import sys

def main():
    """Display anonymizer entry-point guidance."""
    print("RT DICOM Anonymizer module")
    print("Use this module through the CLI or GUI.")
    print("To launch the GUI:")
    print("  python -m rt_dicom_toolkit.gui anonymizer")

if __name__ == "__main__":
    main()
