#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Entry point for the GUI package.
"""

from .validator_gui import run_validator_gui
from .anonymizer_gui import run_anonymizer_gui
import sys

def main():
    """Launch the requested desktop interface."""
    print("RT DICOM Toolkit GUI module")
    print("Usage:")
    print("  validator - launch the validator GUI")
    print("  anonymizer - launch the anonymizer GUI")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validator":
            run_validator_gui()
        elif sys.argv[1] == "anonymizer":
            run_anonymizer_gui()
        else:
            print(f"Unknown command: {sys.argv[1]}")
    else:
        # Launch the validator GUI by default.
        run_validator_gui()

if __name__ == "__main__":
    main()
