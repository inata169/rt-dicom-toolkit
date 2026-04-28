#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RT DICOM Toolkitのメインエントリーポイント
"""

import sys

def main():
    """メインエントリーポイント"""
    if len(sys.argv) == 1:
        # 引数なしの場合はGUI起動
        from .gui import run_app
        run_app()
    else:
        # 引数がある場合はCLIへ委譲
        from .cli import run_anonymizer_cli, run_validator_cli
        if sys.argv[1] == 'validate':
            sys.argv.pop(1)
            run_validator_cli()
        else:
            run_anonymizer_cli()

if __name__ == "__main__":
    main()
