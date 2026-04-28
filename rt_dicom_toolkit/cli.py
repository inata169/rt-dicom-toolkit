"""
RT DICOM Toolkit のコマンドラインインターフェイス
"""

import argparse
import sys
from pathlib import Path

from .anonymizer import RTDicomAnonymizer
from .validator import RTDicomValidator
from .config import (
    DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_LOG_DIR, DEFAULT_REPORT_DIR
)

def run_anonymizer_cli():
    """匿名化ツールのCLIエントリーポイント"""
    parser = argparse.ArgumentParser(description='RT DICOM匿名化ツール')
    parser.add_argument('--input', help='入力ディレクトリのパス', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--output', help='出力ディレクトリのパス', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--log', help='ログディレクトリのパス', default=str(DEFAULT_LOG_DIR))
    parser.add_argument('--level', choices=['full', 'partial'], default='full',
                       help='匿名化レベル: full=完全匿名化, partial=部分匿名化')
    parser.add_argument('--private', choices=['remove', 'keep'], default='remove',
                       help='プライベートタグの処理: remove=削除, keep=保持')
    args = parser.parse_args()
    
    anonymizer = RTDicomAnonymizer()
    anonymizer.input_dir = Path(args.input)
    anonymizer.output_dir = Path(args.output)
    anonymizer.log_dir = Path(args.log)
    
    # 設定を適用
    anonymizer.anonymization_level = args.level
    anonymizer.private_tags = args.private
    
    print(f"入力ディレクトリ: {anonymizer.input_dir}")
    print(f"出力ディレクトリ: {anonymizer.output_dir}")
    print(f"ログディレクトリ: {anonymizer.log_dir}")
    
    anonymizer.process_directory()

def run_validator_cli():
    """検証ツールのCLIエントリーポイント"""
    parser = argparse.ArgumentParser(description='RT DICOM匿名化検証ツール')
    parser.add_argument('--original', help='原本DICOMディレクトリのパス', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--anonymized', help='匿名化DICOMディレクトリのパス', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--report', help='レポート出力ディレクトリのパス', default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()
    
    validator = RTDicomValidator()
    validator.original_dir = Path(args.original)
    validator.anonymized_dir = Path(args.anonymized)
    validator.report_dir = Path(args.report)
    
    print(f"原本ディレクトリ: {validator.original_dir}")
    print(f"匿名化ディレクトリ: {validator.anonymized_dir}")
    print(f"レポートディレクトリ: {validator.report_dir}")
    
    validator.validate_files(validator.original_dir, validator.anonymized_dir)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'validate':
        sys.argv.pop(1)  # 'validate' 引数を削除
        run_validator_cli()
    else:
        run_anonymizer_cli()
