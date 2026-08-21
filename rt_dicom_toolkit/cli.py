"""
Command-line interface for RT DICOM Toolkit.
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
    """Run the anonymizer CLI."""
    parser = argparse.ArgumentParser(description='RT DICOM anonymizer')
    parser.add_argument('--input', help='Input directory path', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--output', help='Output directory path', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--log', help='Log directory path', default=str(DEFAULT_LOG_DIR))
    parser.add_argument('--level', choices=['full', 'partial'], default='full',
                       help='Anonymization level: full or partial')
    parser.add_argument('--private', choices=['remove', 'keep'], default='remove',
                       help='Private-tag handling: remove or keep')
    args = parser.parse_args()
    
    anonymizer = RTDicomAnonymizer()
    anonymizer.input_dir = Path(args.input)
    anonymizer.output_dir = Path(args.output)
    anonymizer.log_dir = Path(args.log)
    
    # Apply the selected settings.
    anonymizer.anonymization_level = args.level
    anonymizer.private_tags = args.private
    
    print(f"Input directory: {anonymizer.input_dir}")
    print(f"Output directory: {anonymizer.output_dir}")
    print(f"Log directory: {anonymizer.log_dir}")
    
    anonymizer.process_directory()

def run_validator_cli():
    """Run the validator CLI."""
    parser = argparse.ArgumentParser(description='RT DICOM anonymization validator')
    parser.add_argument('--original', help='Original DICOM directory path', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--anonymized', help='Anonymized DICOM directory path', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--report', help='Report output directory path', default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()
    
    validator = RTDicomValidator()
    validator.original_dir = Path(args.original)
    validator.anonymized_dir = Path(args.anonymized)
    validator.report_dir = Path(args.report)
    
    print(f"Original directory: {validator.original_dir}")
    print(f"Anonymized directory: {validator.anonymized_dir}")
    print(f"Report directory: {validator.report_dir}")
    
    validator.validate_files(validator.original_dir, validator.anonymized_dir)

def run_template_cli():
    """Run the template synchronization CLI."""
    parser = argparse.ArgumentParser(description='RT DICOM template synchronization tool')
    parser.add_argument('--template', required=True, help='Template DICOM file path')
    parser.add_argument('--input', help='Source DICOM directory or file', default=str(DEFAULT_INPUT_DIR))
    parser.add_argument('--output', help='Output directory path', default=str(DEFAULT_ANONYMOUS_DIR))
    parser.add_argument('--no-patient', action='store_true', help='Do not synchronize patient attributes')
    parser.add_argument('--no-geometry', action='store_true', help='Do not synchronize geometry attributes')
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
        
    print(f"Template: {args.template}")
    print(f"Source: {input_path} ({len(files)} files)")
    print(f"Output: {output_dir}")
    
    for file_path in files:
        try:
            synced_dcm = engine.sync_from_source(
                str(file_path), 
                sync_patient=sync_patient, 
                sync_geometry=sync_geometry
            )
            output_path = output_dir / f"tmpl_{file_path.name}"
            synced_dcm.save_as(str(output_path), write_like_original=False)
            print(f"  Success: {file_path.name} -> {output_path.name}")
        except Exception as e:
            print(f"  Error ({file_path.name}): {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'validate':
            sys.argv.pop(1)  # Remove the 'validate' argument.
            run_validator_cli()
        elif sys.argv[1] == 'template':
            # run_template_cli() parses sys.argv[2:], so do not pop here.
            run_template_cli()
        else:
            run_anonymizer_cli()
    else:
        run_anonymizer_cli()
