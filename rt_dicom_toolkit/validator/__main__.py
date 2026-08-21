#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Entry point for the validator package.
"""

from .core import RTDicomValidator
import sys

def main():
    """Display validator entry-point guidance."""
    print("RT DICOM Validator module")
    print("Use this module through the CLI or GUI.")
    print("To launch the GUI:")
    print("  python -m rt_dicom_toolkit.gui validator")

if __name__ == "__main__":
    main()
