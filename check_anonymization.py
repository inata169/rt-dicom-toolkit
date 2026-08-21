#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DICOM Anonymization Checker

Standalone checker for DICOM anonymization results.
It supports two modes:
1. Standalone scan (--scan): inspect one anonymized directory for identifying data.
2. Paired comparison (--compare): compare original and anonymized files.
"""

import os
import argparse
import json
import traceback
from pathlib import Path
from datetime import datetime

try:
    import pydicom
except ImportError:
    print("Error: pydicom is not installed.")
    print("Install it with: pip install pydicom")
    exit(1)

# Report output directory.
LOG_DIR = Path("DICOM_LOGS")

class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ValidationRules:
    """Rules used by the standalone anonymization checker."""
    def __init__(self):
        # Attributes that must be anonymized.
        self.must_anonymize_tags = [
            "PatientName", "PatientID", "PatientBirthDate", "PatientAddress",
            "PatientTelephoneNumbers", "ReferringPhysicianName", "PhysiciansOfRecord",
            "PerformingPhysicianName", "InstitutionName", "InstitutionAddress",
            "StationName", "OperatorsName"
        ]
        
        # UID attributes.
        self.uid_tags = [
            "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"
        ]
        
        # Date attributes.
        self.date_tags = [
            "StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate"
        ]
        
        # RT-specific attributes.
        self.rt_specific_tags = [
            "StructureSetLabel", "StructureSetName", "ROIName", "PlanLabel"
        ]

class AnonymizationChecker:
    def __init__(self):
        self.rules = ValidationRules()
        LOG_DIR.mkdir(exist_ok=True, parents=True)
    
    def _find_dicom_files(self, directory, exclude_dirs=None):
        """Find DICOM files while excluding selected directories."""
        if exclude_dirs is None:
            exclude_dirs = []
        
        dicom_files = []
        exclude_paths = [Path(d).absolute() for d in exclude_dirs]
        
        for root, _, files in os.walk(directory):
            root_path = Path(root).absolute()
            
            # Skip paths under excluded directories.
            is_excluded = False
            for excl in exclude_paths:
                if str(root_path).startswith(str(excl)):
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
                
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in ['.lnk', '.ini', '.txt', '.log', '.json', '.md']:
                    continue
                    
                # Perform a lightweight DICOM check.
                try:
                    with open(file_path, 'rb') as f:
                        f.seek(128)
                        if f.read(4) == b"DICM":
                            dicom_files.append(file_path)
                        else:
                            # Extensionless DICOM may lack a preamble, so let
                            # pydicom inspect the file.
                            try:
                                pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                                dicom_files.append(file_path)
                            except:
                                pass
                except:
                    pass
        return dicom_files

    def print_colored(self, text, color):
        print(f"{color}{text}{TerminalColors.ENDC}")

    def _check_tag_empty_or_anonymous(self, value):
        """Return whether a value is empty or a known anonymized placeholder."""
        val_str = str(value).strip().upper()
        if not val_str:
            return True
        if "ANONYMOUS" in val_str or "ANON" in val_str:
            return True
        if val_str == "19000101" or val_str == "20000101":
            return True
        # Placeholders such as 000Y for age and O for sex.
        if val_str in ["000Y", "O"]:
            return True
        return False

    def scan_directory(self, target_dir):
        """Run standalone scan mode."""
        target_dir = Path(target_dir)
        if not target_dir.exists():
            self.print_colored(f"Error: directory does not exist -> {target_dir}", TerminalColors.FAIL)
            return None

        self.print_colored(f"Starting scan: {target_dir}", TerminalColors.OKCYAN)
        files = self._find_dicom_files(target_dir)
        self.print_colored(f"Files to scan: {len(files)}", TerminalColors.OKCYAN)
        
        results = {
            "mode": "scan",
            "target_dir": str(target_dir),
            "scanned_files": len(files),
            "warnings": [],
            "errors": [],
            "stats": {
                "private_tags_found": 0,
                "suspicious_must_tags": 0,
                "files_with_issues": set()
            },
            "file_details": []
        }
        
        for file_path in files:
            try:
                dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                file_issues = []
                
                # Check private tags.
                private_tags = [tag for tag in dcm.keys() if tag.is_private]
                if private_tags:
                    results["stats"]["private_tags_found"] += len(private_tags)
                    file_issues.append(f"{len(private_tags)} private tags remain")
                
                # Check required attributes.
                for tag in self.rules.must_anonymize_tags:
                    if hasattr(dcm, tag):
                        val = getattr(dcm, tag)
                        if not self._check_tag_empty_or_anonymous(val):
                            results["stats"]["suspicious_must_tags"] += 1
                            # Patient ID may be hashed, so report a warning rather
                            # than treating every unknown value as a hard error.
                            if tag == "PatientID":
                                if not str(val).isdigit() or len(str(val)) < 5:
                                    file_issues.append(f"Possibly incomplete Patient ID: {val}")
                            else:
                                file_issues.append(f"Possible identifying data remains ({tag}): {val}")
                
                # Check date attributes.
                for tag in self.rules.date_tags:
                    if hasattr(dcm, tag):
                        val = getattr(dcm, tag)
                        if str(val) != "20000101" and str(val) != "":
                            file_issues.append(f"Possible real date remains ({tag}): {val}")

                # Accept configured known generated UID roots. This check uses
                # the root generated by pydicom.
                for tag in self.rules.uid_tags:
                    if hasattr(dcm, tag):
                        val = str(getattr(dcm, tag))
                        if not val.startswith("1.2.826.0.1.3680043.8.498") and not val.startswith("2.25."):
                             file_issues.append(f"Possible original UID remains ({tag}): {val}")

                detail = {"file": str(file_path.name), "issues": file_issues}
                results["file_details"].append(detail)
                
                if file_issues:
                    results["stats"]["files_with_issues"].add(str(file_path.name))
                    for issue in file_issues:
                        results["warnings"].append(f"{file_path.name}: {issue}")

            except Exception as e:
                results["errors"].append(f"Read error for {file_path.name}: {str(e)}")
        
        # Convert sets to lists for serialization.
        results["stats"]["files_with_issues"] = list(results["stats"]["files_with_issues"])
        return results

    def _generate_matching_key(self, dcm):
        key_parts = []
        if hasattr(dcm, 'Modality'): key_parts.append(f"MOD:{dcm.Modality}")
        if hasattr(dcm, 'SeriesNumber'): key_parts.append(f"SER:{dcm.SeriesNumber}")
        if hasattr(dcm, 'InstanceNumber'): key_parts.append(f"INS:{dcm.InstanceNumber}")
        if hasattr(dcm, 'SOPClassUID'): key_parts.append(f"SOP:{dcm.SOPClassUID}")
        
        # Use Image Position Patient and similar values when available.
        if hasattr(dcm, 'ImagePositionPatient'):
            pos = [str(int(float(p))) for p in dcm.ImagePositionPatient]
            key_parts.append(f"POS:{','.join(pos)}")
            
        if len(key_parts) >= 2:
            return "|".join(key_parts)
        return None

    def compare_directories(self, original_dir, anonymized_dir):
        """Run paired-comparison mode."""
        orig_dir = Path(original_dir)
        anon_dir = Path(anonymized_dir)
        
        if not orig_dir.exists() or not anon_dir.exists():
            self.print_colored("Error: one or both specified directories do not exist.", TerminalColors.FAIL)
            return None
            
        self.print_colored("Starting paired comparison:", TerminalColors.OKCYAN)
        self.print_colored(f"  Original: {orig_dir}", TerminalColors.OKCYAN)
        self.print_colored(f"  Anonymized: {anon_dir}", TerminalColors.OKCYAN)
        
        orig_files = self._find_dicom_files(orig_dir, exclude_dirs=[anon_dir])
        anon_files = self._find_dicom_files(anon_dir)
        
        self.print_colored(f"Original files: {len(orig_files)}", TerminalColors.OKCYAN)
        self.print_colored(f"Anonymized files: {len(anon_files)}", TerminalColors.OKCYAN)
        
        results = {
            "mode": "compare",
            "original_dir": str(orig_dir),
            "anonymized_dir": str(anon_dir),
            "original_files_count": len(orig_files),
            "anonymized_files_count": len(anon_files),
            "matched_files": 0,
            "stats": {
                "must_tags_changed": 0,
                "must_tags_unchanged": 0,
                "uids_changed": 0,
                "uids_unchanged": 0,
                "private_tags_removed": 0,
                "private_tags_remaining": 0
            },
            "warnings": [],
            "errors": [],
            "file_details": []
        }
        
        # Build matching indexes.
        orig_map = {}
        for f in orig_files:
            try:
                dcm = pydicom.dcmread(str(f), force=True, stop_before_pixels=True)
                key = self._generate_matching_key(dcm)
                if key:
                    orig_map[key] = f
            except:
                pass
                
        for anon_f in anon_files:
            try:
                anon_dcm = pydicom.dcmread(str(anon_f), force=True, stop_before_pixels=True)
                key = self._generate_matching_key(anon_dcm)
                orig_f = None
                
                # Prefer a direct file-name match.
                expected_orig = orig_dir / anon_f.name
                if expected_orig in orig_files:
                    orig_f = expected_orig
                elif key and key in orig_map:
                    orig_f = orig_map[key]
                
                if not orig_f:
                    results["warnings"].append(f"No matching original file: {anon_f.name}")
                    continue
                    
                results["matched_files"] += 1
                orig_dcm = pydicom.dcmread(str(orig_f), force=True, stop_before_pixels=True)
                
                detail = {"file": anon_f.name, "diffs": []}
                
                # Compare required attributes.
                for tag in self.rules.must_anonymize_tags:
                    orig_val = getattr(orig_dcm, tag, "N/A") if hasattr(orig_dcm, tag) else "N/A"
                    anon_val = getattr(anon_dcm, tag, "N/A") if hasattr(anon_dcm, tag) else "N/A"
                    
                    if str(orig_val) != str(anon_val):
                        results["stats"]["must_tags_changed"] += 1
                    else:
                        if orig_val != "N/A" and str(orig_val).strip() != "":
                            results["stats"]["must_tags_unchanged"] += 1
                            detail["diffs"].append(f"Required attribute unchanged ({tag}): {orig_val}")
                            
                # Compare UIDs.
                for tag in self.rules.uid_tags:
                    orig_val = getattr(orig_dcm, tag, "N/A") if hasattr(orig_dcm, tag) else "N/A"
                    anon_val = getattr(anon_dcm, tag, "N/A") if hasattr(anon_dcm, tag) else "N/A"
                    if str(orig_val) != str(anon_val):
                        results["stats"]["uids_changed"] += 1
                    else:
                        if orig_val != "N/A":
                            results["stats"]["uids_unchanged"] += 1
                            detail["diffs"].append(f"UID unchanged ({tag}): {orig_val}")
                            
                # Check private tags.
                orig_priv = [t for t in orig_dcm.keys() if t.is_private]
                anon_priv = [t for t in anon_dcm.keys() if t.is_private]
                
                if len(orig_priv) > 0 and len(anon_priv) == 0:
                    results["stats"]["private_tags_removed"] += 1
                elif len(anon_priv) > 0:
                    results["stats"]["private_tags_remaining"] += 1
                    detail["diffs"].append(f"Private tags remain: {len(anon_priv)}")
                
                if detail["diffs"]:
                    results["file_details"].append(detail)
                    
            except Exception as e:
                results["errors"].append(f"Processing error for {anon_f.name}: {str(e)}")
                
        return results

    def generate_report(self, results):
        if not results:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"checker_scan_{timestamp}" if results["mode"] == "scan" else f"checker_compare_{timestamp}"
        
        # 1. Console Output
        self.print_colored("\n" + "="*40, TerminalColors.HEADER)
        self.print_colored(" Anonymization Checker Report", TerminalColors.BOLD)
        self.print_colored("="*40, TerminalColors.HEADER)
        
        if results["mode"] == "scan":
            self.print_colored("Mode: standalone scan", TerminalColors.OKCYAN)
            self.print_colored(f"Scan target: {results['target_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"Files: {results['scanned_files']}", TerminalColors.OKCYAN)
            
            stats = results["stats"]
            issues_count = len(stats["files_with_issues"])
            
            if issues_count == 0 and not results["errors"]:
                self.print_colored("\n✅ No configured identifying data was detected in the scanned files.", TerminalColors.OKGREEN)
            else:
                self.print_colored(f"\n⚠️ Files with possible issues: {issues_count}", TerminalColors.WARNING)
                self.print_colored(f"  - Remaining private tags: {stats['private_tags_found']}", TerminalColors.WARNING)
                self.print_colored(f"  - Suspicious required attributes: {stats['suspicious_must_tags']}", TerminalColors.WARNING)
                
        else:
            self.print_colored("Mode: paired comparison", TerminalColors.OKCYAN)
            self.print_colored(f"Original: {results['original_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"Anonymized: {results['anonymized_dir']}", TerminalColors.OKCYAN)
            self.print_colored(f"Matched files: {results['matched_files']}/{results['anonymized_files_count']}", TerminalColors.OKCYAN)
            
            stats = results["stats"]
            self.print_colored("\n[Change statistics]", TerminalColors.BOLD)
            self.print_colored(f"  Required attributes changed: {stats['must_tags_changed']} / unchanged: {stats['must_tags_unchanged']}", TerminalColors.OKBLUE)
            self.print_colored(f"  UIDs changed: {stats['uids_changed']} / unchanged: {stats['uids_unchanged']}", TerminalColors.OKBLUE)
            
            if stats["must_tags_unchanged"] == 0 and stats["uids_unchanged"] == 0 and stats["private_tags_remaining"] == 0:
                self.print_colored("\n✅ Paired validation passed.", TerminalColors.OKGREEN)
            else:
                self.print_colored("\n⚠️ Some configured values may be insufficiently anonymized.", TerminalColors.WARNING)

        if results["errors"]:
            self.print_colored("\n❌ Errors occurred:", TerminalColors.FAIL)
            for err in results["errors"][:5]:
                self.print_colored(f"  {err}", TerminalColors.FAIL)
            if len(results["errors"]) > 5:
                self.print_colored(f"  ...and {len(results['errors']) - 5} more", TerminalColors.FAIL)

        # 2. Markdown Report
        md_path = LOG_DIR / f"{prefix}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# DICOM Anonymization Checker Report\n\n")
            f.write(f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Mode**: {results['mode']}\n")
            
            if results["mode"] == "scan":
                f.write(f"- **Target Directory**: `{results['target_dir']}`\n")
                f.write(f"- **Scanned Files**: {results['scanned_files']}\n\n")
                f.write("## Summary\n")
                
                stats = results["stats"]
                if len(stats["files_with_issues"]) == 0:
                    f.write("✅ **No personal information found in any files.**\n\n")
                else:
                    f.write("⚠️ **Potential issues detected!**\n\n")
                    f.write(f"- Files with issues: {len(stats['files_with_issues'])}\n")
                    f.write(f"- Private tags found: {stats['private_tags_found']}\n")
                    f.write(f"- Suspicious must-anonymize tags: {stats['suspicious_must_tags']}\n\n")
                    
                    f.write("## Details\n")
                    for warn in results["warnings"][:20]:
                        f.write(f"- {warn}\n")
                    if len(results["warnings"]) > 20:
                         f.write(f"- ...and {len(results['warnings']) - 20} more warnings.\n")
            else:
                f.write(f"- **Original Directory**: `{results['original_dir']}`\n")
                f.write(f"- **Anonymized Directory**: `{results['anonymized_dir']}`\n")
                f.write(f"- **Matched Files**: {results['matched_files']}\n\n")
                
                stats = results["stats"]
                f.write("## Statistics\n")
                f.write(f"- Must-anonymize tags changed: {stats['must_tags_changed']}\n")
                f.write(f"- Must-anonymize tags unchanged: {stats['must_tags_unchanged']}\n")
                f.write(f"- UID tags changed: {stats['uids_changed']}\n")
                f.write(f"- UID tags unchanged: {stats['uids_unchanged']}\n")
                f.write(f"- Private tags removed (files): {stats['private_tags_removed']}\n")
                f.write(f"- Private tags remaining (files): {stats['private_tags_remaining']}\n\n")
                
                if stats["must_tags_unchanged"] > 0 or stats["uids_unchanged"] > 0:
                    f.write("⚠️ **Warning: Some tags were not changed!**\n\n")
                    f.write("## Details\n")
                    for d in results["file_details"][:20]:
                        f.write(f"### {d['file']}\n")
                        for diff in d["diffs"]:
                            f.write(f"- {diff}\n")
                    if len(results["file_details"]) > 20:
                        f.write(f"\n...and {len(results['file_details']) - 20} more files with issues.\n")
            
            if results["errors"]:
                f.write("\n## Errors\n")
                for err in results["errors"]:
                    f.write(f"- `{err}`\n")

        # 3. Text Report (Simple copy of Markdown for ease of use)
        txt_path = LOG_DIR / f"{prefix}.txt"
        import shutil
        shutil.copy(md_path, txt_path)

        # 4. JSON Report (Full details)
        json_path = LOG_DIR / f"{prefix}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            # Set is already converted to list
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.print_colored("\nReports written:", TerminalColors.OKGREEN)
        self.print_colored(f"  - Markdown: {md_path}", TerminalColors.OKGREEN)
        self.print_colored(f"  - Text: {txt_path}", TerminalColors.OKGREEN)
        self.print_colored(f"  - JSON: {json_path}", TerminalColors.OKGREEN)

def main():
    parser = argparse.ArgumentParser(description="DICOM Anonymization Checker")
    parser.add_argument("--scan", type=str, metavar="DIR", help="Scan an anonymized directory for configured identifying data")
    parser.add_argument("--compare", nargs=2, metavar=("ORIG_DIR", "ANON_DIR"), help="Compare original and anonymized files")
    
    args = parser.parse_args()
    checker = AnonymizationChecker()
    
    if args.scan:
        res = checker.scan_directory(args.scan)
        checker.generate_report(res)
    elif args.compare:
        res = checker.compare_directories(args.compare[0], args.compare[1])
        checker.generate_report(res)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
