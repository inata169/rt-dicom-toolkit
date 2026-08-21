#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for RT DICOM Toolkit.
"""

import sys

def main():
    """Launch the GUI without arguments or dispatch to the CLI."""
    if len(sys.argv) == 1:
        # Launch the GUI when no arguments are supplied.
        from .gui import run_app
        run_app()
    else:
        # Delegate argument-based use to the CLI.
        from .cli import run_anonymizer_cli, run_validator_cli, run_template_cli
        if sys.argv[1] == 'validate':
            sys.argv.pop(1)
            run_validator_cli()
        elif sys.argv[1] == 'template':
            # run_template_cli() parses sys.argv[2:].
            run_template_cli()
        else:
            run_anonymizer_cli()

if __name__ == "__main__":
    main()
