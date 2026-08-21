"""
Matplotlib configuration utilities.
"""

import matplotlib.pyplot as plt
import matplotlib
import os
import sys
import platform

def configure_matplotlib_for_japanese():
    """Configure portable fonts for the English interface.

    The function name is retained for backward compatibility.
    """
    matplotlib.rcParams['font.family'] = ['sans-serif']

    # Keep text editable in PDF and PostScript output.
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    # Render the Unicode minus sign correctly.
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    return True
