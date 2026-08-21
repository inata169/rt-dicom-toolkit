"""
Core DICOM anonymization validation.
"""

import os
import json
from pathlib import Path
from datetime import datetime
import logging
import traceback
import threading

import pydicom
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ..config import (
    DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_REPORT_DIR
)
from .rules import ValidationRules
from .report import generate_summary_report
from ..utils.logging_utils import setup_logger
from ..utils.file_utils import find_dicom_files

class RTDicomValidator:
    """Validate anonymized radiotherapy DICOM files."""
    
    def __init__(self, root=None):
        """
        Initialize the validator.
        
        Args:
            root: Optional Tkinter root; use None in CLI mode.
        """
        self.root = root
        
        # Directory settings.
        self.original_dir = DEFAULT_INPUT_DIR
        self.anonymized_dir = DEFAULT_ANONYMOUS_DIR
        self.report_dir = DEFAULT_REPORT_DIR
        
        # Create the report directory when absent.
        self.report_dir.mkdir(exist_ok=True)
        
        # Logger configuration.
        self.logger = setup_logger("RTDicomValidator")
        
        # Validation rules.
        self.rules = ValidationRules()
        
        # GUI-bound state.
        if self.root:
            self.log_text = None
            self.summary_text = None
            self.tree = None
            self.figure = None
            self.ax = None
            self.canvas = None
            self.anonymization_level = None
            self.check_private_tags = None
            self.check_file_structure = None
            self.check_uid_changed = None
            self.detailed_report = None
            self.status_var = None
            
        self.log_message("Anonymization validator initialized")
        self.log_message(f"Initial original directory: {self.original_dir}")
        self.log_message(f"Initial anonymized directory: {self.anonymized_dir}")
        self.log_message(f"Initial report directory: {self.report_dir}")
    
    def log_message(self, message):
        """Write a message to the GUI callback and logger."""
        try:
            if self.root and hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.root.update_idletasks()
            
            # Always write through the configured logger.
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"Logging error: {str(e)}")
    
    def update_summary(self, message):
        """Update summary text through the GUI callback."""
        try:
            if self.root and hasattr(self, 'summary_text') and self.summary_text:
                self.summary_text.insert("end", message + "\n")
                self.summary_text.see("end")
                self.root.update_idletasks()
        except Exception as e:
            print(f"Summary update error: {str(e)}")
    
    def compare_dicom_files(self, original_file, anonymized_file):
        """
        Compare original and anonymized DICOM files.
        
        Args:
            original_file: Original DICOM file path.
            anonymized_file: Anonymized DICOM file path.
            
        Returns:
            Dictionary of validation results.
        """
        try:
            # Read both files.
            original_dcm = pydicom.dcmread(str(original_file), force=True)
            anonymized_dcm = pydicom.dcmread(str(anonymized_file), force=True)
            
            # Initialize results.
            results = {
                "must_anonymize": {},  # Required anonymization attributes.
                "uid_tags": {},        # UID results.
                "structure_tags": {},  # Structure results.
                "optional_tags": {},   # Optional-attribute results.
                "rt_specific_tags": {}, # RT-specific results.
                "private_tags": {      # Private-tag results.
                    "original_count": 0,
                    "anonymized_count": 0
                },
                "pixel_data": {        # Pixel comparison results.
                    "original_shape": None,
                    "anonymized_shape": None,
                    "match": False
                }
            }
            
            # Check required anonymization attributes.
            for tag in self.rules.must_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Determine whether the value was anonymized.
                anonymized = False
                if str(anonymized_value) == "N/A":
                    status = "removed"
                    anonymized = True
                elif str(anonymized_value) == "":
                    status = "cleared"
                    anonymized = True
                elif str(original_value) != str(anonymized_value):
                    status = "changed"
                    anonymized = True
                else:
                    status = "unchanged"
                
                results["must_anonymize"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "anonymized": anonymized
                }
            
            # Check UID attributes.
            for tag in self.rules.uid_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Determine whether the UID changed.
                changed = False
                if str(anonymized_value) == "N/A":
                    status = "removed"
                elif str(original_value) != str(anonymized_value):
                    status = "changed"
                    changed = True
                else:
                    status = "unchanged"
                
                results["uid_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "changed": changed
                }
            
            # Check preserved structure attributes.
            for tag in self.rules.structure_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Determine whether the value was preserved.
                preserved = False
                if str(original_value) == str(anonymized_value):
                    status = "preserved"
                    preserved = True
                else:
                    status = "changed"
                
                results["structure_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "preserved": preserved
                }
            
            # Check optional attributes. Use the GUI setting when available,
            # otherwise default to the full profile.
            anonymization_level = getattr(self, 'anonymization_level', None)
            if anonymization_level and hasattr(anonymization_level, 'get'):
                level = anonymization_level.get()
            else:
                level = "full"
                
            for tag in self.rules.optional_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Evaluate according to the selected profile.
                if level == "full":
                    # Full mode expects a changed value.
                    changed = False
                    if str(anonymized_value) == "N/A":
                        status = "removed"
                        changed = True
                    elif str(original_value) != str(anonymized_value):
                        status = "changed"
                        changed = True
                    else:
                        status = "unchanged"
                else:
                    # Partial mode may preserve the value.
                    changed = True
                    if str(original_value) == str(anonymized_value):
                        status = "preserved"
                    else:
                        status = "changed"
                
                results["optional_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status,
                    "changed": changed
                }
            
            # Check RT-specific attributes.
            for tag in self.rules.rt_specific_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # ROI Name requires special handling because some anatomy names
                # may be preserved.
                if tag == "ROIName":
                    status = "special handling"
                    # Selected anatomy names such as heart and lung are preserved.
                    if "N/A" not in str(original_value):
                        organs = ["lung", "heart", "liver", "kidney", "spinal", "brain"]
                        if any(organ in str(original_value).lower() for organ in organs):
                            if str(original_value) == str(anonymized_value):
                                status = "correctly preserved"
                            else:
                                status = "expected anatomy name changed"
                        else:
                            if str(original_value) != str(anonymized_value):
                                status = "correctly anonymized"
                            else:
                                status = "not anonymized"
                else:
                    # Other configured RT attributes should be anonymized.
                    if str(anonymized_value) == "N/A":
                        status = "removed"
                    elif str(original_value) != str(anonymized_value):
                        status = "changed"
                    else:
                        status = "unchanged"
                
                results["rt_specific_tags"][tag] = {
                    "original": str(original_value),
                    "anonymized": str(anonymized_value),
                    "status": status
                }
            
            # Check private tags.
            original_private_tags = [tag for tag in original_dcm.keys() if tag.is_private]
            anonymized_private_tags = [tag for tag in anonymized_dcm.keys() if tag.is_private]
            
            results["private_tags"]["original_count"] = len(original_private_tags)
            results["private_tags"]["anonymized_count"] = len(anonymized_private_tags)
            
            # Compare Pixel Data when present.
            if hasattr(original_dcm, 'PixelData') and hasattr(anonymized_dcm, 'PixelData'):
                try:
                    # Inspect Transfer Syntax UID.
                    original_transfer_syntax = None
                    anonymized_transfer_syntax = None
                    
                    # Read it only from available file meta.
                    if hasattr(original_dcm, 'file_meta') and hasattr(original_dcm.file_meta, 'TransferSyntaxUID'):
                        original_transfer_syntax = original_dcm.file_meta.TransferSyntaxUID
                    
                    if hasattr(anonymized_dcm, 'file_meta') and hasattr(anonymized_dcm.file_meta, 'TransferSyntaxUID'):
                        anonymized_transfer_syntax = anonymized_dcm.file_meta.TransferSyntaxUID
                    
                    # Warn when transfer syntax differs.
                    if original_transfer_syntax != anonymized_transfer_syntax:
                        self.logger.warning(f"Transfer syntax differs: original={original_transfer_syntax}, anonymized={anonymized_transfer_syntax}")
                    
                    # Compare decoded pixel arrays.
                    original_pixel_array = original_dcm.pixel_array
                    anonymized_pixel_array = anonymized_dcm.pixel_array
                    
                    results["pixel_data"]["original_shape"] = original_pixel_array.shape
                    results["pixel_data"]["anonymized_shape"] = anonymized_pixel_array.shape
                    
                    # Compare array shapes.
                    if original_pixel_array.shape == anonymized_pixel_array.shape:
                        # Compare pixel values.
                        if np.array_equal(original_pixel_array, anonymized_pixel_array):
                            results["pixel_data"]["match"] = True
                except Exception as e:
                    self.logger.warning(f"Error comparing Pixel Data: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"DICOM comparison error: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _generate_matching_key(self, dcm):
        """
        Generate a matching key from a DICOM dataset.
        
        Args:
            dcm: Dataset loaded by pydicom.
            
        Returns:
            Matching-key string, or None when data is insufficient.
        """
        try:
            # Use Modality, Series Number, Instance Number, and related values.
            key_parts = []
            
            # Modality.
            if hasattr(dcm, 'Modality'):
                key_parts.append(f"MOD:{dcm.Modality}")
            
            # Series Number.
            if hasattr(dcm, 'SeriesNumber'):
                key_parts.append(f"SER:{dcm.SeriesNumber}")
            
            # Instance Number.
            if hasattr(dcm, 'InstanceNumber'):
                key_parts.append(f"INS:{dcm.InstanceNumber}")
            
            # Image or slice position.
            if hasattr(dcm, 'ImagePositionPatient'):
                # Convert to a stable string without decimal detail.
                pos = [str(int(float(p))) for p in dcm.ImagePositionPatient]
                key_parts.append(f"POS:{','.join(pos)}")
            
            # SOP Class UID identifies the object type.
            if hasattr(dcm, 'SOPClassUID'):
                key_parts.append(f"SOP:{dcm.SOPClassUID}")
            
            # Require at least two components for a usable key.
            if len(key_parts) >= 2:
                return "|".join(key_parts)
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Matching-key generation error: {e}")
            return None

    def validate_files(self, original_dir, anonymized_dir):
        """
        Validate files in the original and anonymized directories.
        
        Args:
            original_dir: Original DICOM directory path.
            anonymized_dir: Anonymized DICOM directory path.
            
        Returns:
            Validation summary text.
        """
        try:
            # Discover original DICOM files.
            original_files = find_dicom_files(original_dir)
            
            # Discover anonymized DICOM files.
            anonymized_files = find_dicom_files(anonymized_dir)
            
            self.log_message(f"Original DICOM files: {len(original_files)}")
            self.log_message(f"Anonymized DICOM files: {len(anonymized_files)}")
            
            # Aggregated analysis data.
            summary = {
                "total_files": len(original_files),
                "matched_files": 0,
                "must_anonymize_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rules.must_anonymize_tags},
                "uid_stats": {tag: {"changed": 0, "not_changed": 0} for tag in self.rules.uid_tags},
                "structure_stats": {tag: {"preserved": 0, "not_preserved": 0} for tag in self.rules.structure_tags},
                "private_tags_stats": {"removed": 0, "not_removed": 0},
                "modality_stats": {},
                "rt_specific_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rules.rt_specific_tags},
                "patient_id_map": {},
            }
            
            # Per-file detailed results.
            detailed_results = []
            
            # Match original and anonymized files.
            progress_count = 0
            
            # Match by relative path first, then by DICOM attributes.
            original_files_map = {}
            original_files_info = {}
            
            # Index original files.
            for file_path in original_files:
                # Relative-path index.
                rel_path = file_path.relative_to(original_dir)
                original_files_map[str(rel_path)] = file_path
                
                # DICOM-attribute index.
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                    key = self._generate_matching_key(dcm)
                    if key:
                        original_files_info[key] = file_path
                except Exception as e:
                    self.logger.warning(f"Error reading original file: {file_path} - {e}")
            
            # Match and validate anonymized files.
            for anon_file in anonymized_files:
                progress_count += 1
                
                # Update progress.
                if self.root and hasattr(self, 'status_var') and self.status_var:
                    progress = progress_count / len(anonymized_files) * 100
                    self.status_var.set(f"Validating... {progress_count}/{len(anonymized_files)} ({progress:.1f}%)")
                
                try:
                    # Build the anonymized relative path.
                    rel_path = anon_file.relative_to(anonymized_dir)
                    orig_file = None
                    
                    # First match by path.
                    if str(rel_path) in original_files_map:
                        orig_file = original_files_map[str(rel_path)]
                        self.log_message(f"Matched by path: {rel_path}")
                    else:
                        # Then match by DICOM attributes.
                        try:
                            dcm = pydicom.dcmread(str(anon_file), force=True, stop_before_pixels=True)
                            key = self._generate_matching_key(dcm)
                            if key and key in original_files_info:
                                orig_file = original_files_info[key]
                                self.log_message(f"Matched by attributes: {anon_file.name} -> {orig_file.name}")
                        except Exception as e:
                            self.logger.warning(f"Error reading anonymized file: {anon_file} - {e}")
                    
                    # Validate a matched pair.
                    if orig_file:
                        
                        self.log_message(f"Validating: {rel_path}")
                        
                        # Compare the pair.
                        results = self.compare_dicom_files(orig_file, anon_file)
                        
                        if results:
                            summary["matched_files"] += 1
                            
                            # Update Modality statistics.
                            try:
                                orig_dcm = pydicom.dcmread(str(orig_file), force=True)
                                if hasattr(orig_dcm, 'Modality'):
                                    modality = orig_dcm.Modality
                                    if modality not in summary["modality_stats"]:
                                        summary["modality_stats"][modality] = 1
                                    else:
                                        summary["modality_stats"][modality] += 1
                            except:
                                pass
                            
                            # Required-attribute statistics.
                            for tag, info in results["must_anonymize"].items():
                                if info["anonymized"]:
                                    summary["must_anonymize_stats"][tag]["anonymized"] += 1
                                else:
                                    summary["must_anonymize_stats"][tag]["not_anonymized"] += 1
                            
                            # UID statistics.
                            for tag, info in results["uid_tags"].items():
                                if info["changed"]:
                                    summary["uid_stats"][tag]["changed"] += 1
                                else:
                                    summary["uid_stats"][tag]["not_changed"] += 1
                            
                            # Structure statistics.
                            for tag, info in results["structure_tags"].items():
                                if info["preserved"]:
                                    summary["structure_stats"][tag]["preserved"] += 1
                                else:
                                    summary["structure_stats"][tag]["not_preserved"] += 1
                            
                            # Private-tag statistics.
                            if results["private_tags"]["anonymized_count"] == 0:
                                summary["private_tags_stats"]["removed"] += 1
                            else:
                                summary["private_tags_stats"]["not_removed"] += 1
                            
                            # Update patient-ID mapping.
                            if "PatientID" in results["must_anonymize"]:
                                orig_id = results["must_anonymize"]["PatientID"]["original"]
                                anon_id = results["must_anonymize"]["PatientID"]["anonymized"]
                                
                                if orig_id != "N/A" and anon_id != "N/A":
                                    summary["patient_id_map"][orig_id] = anon_id
                            
                            # Add detailed results.
                            detailed_report = True
                            if hasattr(self, 'detailed_report') and hasattr(self.detailed_report, 'get'):
                                detailed_report = self.detailed_report.get()
                                
                            if detailed_report:
                                detailed_results.append({
                                    "original_file": str(orig_file),
                                    "anonymized_file": str(anon_file),
                                    "results": results
                                })
                            
                            # Update the GUI tree when available.
                            if self.root and hasattr(self, 'update_treeview'):
                                # Clear only for the first file.
                                clear = (progress_count == 1)
                                self.update_treeview(results, clear=clear)
                    else:
                        self.log_message(f"No matching file: {rel_path}")
                
                except Exception as e:
                    self.log_message(f"File-validation error: {str(e)}")
                    self.logger.error(traceback.format_exc())
            
            # Generate the summary report.
            report = generate_summary_report(summary, self.rules)
            
            # Save the detailed report.
            detailed_report = True
            if hasattr(self, 'detailed_report') and hasattr(self.detailed_report, 'get'):
                detailed_report = self.detailed_report.get()
                
            if detailed_report:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                detailed_report_path = Path(self.report_dir) / f"detailed_validation_report_{timestamp}.json"
                
                with open(detailed_report_path, 'w', encoding='utf-8') as f:
                    json.dump(detailed_results, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"Saved detailed report: {detailed_report_path}")
            
            # Render charts when a GUI is active.
            if self.root and hasattr(self, 'draw_validation_graphs'):
                self.draw_validation_graphs(summary)
            
            return report
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            return None
