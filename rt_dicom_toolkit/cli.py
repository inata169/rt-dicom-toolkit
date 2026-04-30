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

def run_template_cli():
    """テンプレート適用のCLIエントリーポイント"""
    parser = argparse.ArgumentParser(description='RT DICOMテンプレート合成ツール')
    parser.add_argument('--template', required=True, help='テンプレートDICOMファイルのパス')
    parser.add_argument('--input', help='情報抽出元のDICOMディレクトリまたはファイル', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--output', help='出力ディレクトリのパス', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--no-patient', action='store_true', help='患者情報を同期しない')
    parser.add_argument('--no-geometry', action='store_true', help='幾何学情報を同期しない')
    args = parser.parse_args(sys.argv[2:])
    
    from .template.engine import DICOMTemplateEngine
    from .utils.file_utils import find_dicom_files
    
    engine = DICOMTemplateEngine(args.template)
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sync_patient = not args.no_patient
    sync_geometry = not args.no_geometry
    
    if input_path.is_file():
        files = [input_path]
    else:
        files = find_dicom_files(input_path)
        
    print(f"テンプレート: {args.template}")
    print(f"抽出元: {input_path} ({len(files)} ファイル)")
    print(f"出力先: {output_dir}")
    
    for file_path in files:
        try:
            synced_dcm = engine.sync_from_source(
                str(file_path), 
                sync_patient=sync_patient, 
                sync_geometry=sync_geometry
            )
            output_path = output_dir / f"tmpl_{file_path.name}"
            synced_dcm.save_as(str(output_path), write_like_original=False)
            print(f"  成功: {file_path.name} -> {output_path.name}")
        except Exception as e:
            print(f"  エラー ({file_path.name}): {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'validate':
            sys.argv.pop(1)  # 'validate' 引数を削除
            run_validator_cli()
        elif sys.argv[1] == 'template':
            # run_template_cli() 内で parse_args(sys.argv[2:]) を行うためここではpopしない
            run_template_cli()
        else:
            run_anonymizer_cli()
    else:
        run_anonymizer_cli()
