"""
Core DICOM anonymization functionality.
"""

import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
import logging
import traceback
import threading

import pydicom
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
from pydicom.dataset import FileMetaDataset

from ..config import (
    DEFAULT_INPUT_DIR, DEFAULT_ANONYMOUS_DIR, DEFAULT_LOG_DIR,
    DEFAULT_ANONYMIZATION_LEVEL, DEFAULT_PRIVATE_TAGS_HANDLING, 
    DEFAULT_UID_HANDLING, DEFAULT_KEEP_STRUCTURE, DEFAULT_PATIENT_ID_METHOD
)
from .profiles import get_anonymization_profile
from ..utils.logging_utils import setup_logger
from ..utils.file_utils import find_dicom_files

class RTDicomAnonymizer:
    """Anonymize radiotherapy DICOM files."""
    
    def __init__(self, root=None):
        """
        Initialize the anonymizer.
        
        Args:
            root: Optional Tkinter root; use None in CLI mode.
        """
        self.root = root
        
        # Directory settings.
        self.input_dir = DEFAULT_INPUT_DIR
        self.output_dir = DEFAULT_ANONYMOUS_DIR
        self.log_dir = DEFAULT_LOG_DIR
        
        # Anonymization settings.
        self.anonymization_level = DEFAULT_ANONYMIZATION_LEVEL
        self.private_tags = DEFAULT_PRIVATE_TAGS_HANDLING
        self.uid_handling = DEFAULT_UID_HANDLING
        self.keep_structure = DEFAULT_KEEP_STRUCTURE
        self.patient_id_method = DEFAULT_PATIENT_ID_METHOD
        
        # Processing state.
        self.patient_id_map = {}
        self.next_patient_id = 9000001
        self.uid_map = {}
        
        # Logger configuration.
        self.logger = setup_logger("RTDicomAnonymizer")
        self.log_callback = None
        
        # GUI-bound state.
        if self.root:
            self.log_text = None
            self.progress_var = None
            self.status_var = None
            
        self.log_message("Anonymizer initialized")
        self.log_message(f"Initial input directory: {self.input_dir}")
        self.log_message(f"Initial output directory: {self.output_dir}")
        self.log_message(f"Initial log directory: {self.log_dir}")
    
    def log_message(self, message):
        """Write a message to the GUI callback and logger."""
        try:
            if self.log_callback:
                self.log_callback(message)
                
            if self.root and hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.root.update_idletasks()
            
            # Always write through the configured logger.
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"Logging error: {str(e)}")
    
    def generate_anonymous_id(self, original_id):
        """
        Generate an anonymized ID from an original patient ID.
        
        Args:
            original_id: Original patient ID.
            
        Returns:
            Anonymized patient ID.
        """
        # Reuse an existing mapping.
        if str(original_id) in self.patient_id_map:
            return self.patient_id_map[str(original_id)]
        
        if self.patient_id_method == "sequential":
            if not hasattr(self, 'patient_counter'):
                self.patient_counter = 0
            self.patient_counter += 1
            new_id = f"Patient_{self.patient_counter:03d}"
        else:
            # Generate the next sequential ID, starting at 9000001.
            if self.next_patient_id > 9999999:
                # Fall back to a hash when the sequence is exhausted.
                hash_id = int(hashlib.md5(str(original_id).encode()).hexdigest(), 16) % 1000000
                new_id = f"9{hash_id:06d}"
            else:
                new_id = str(self.next_patient_id)
                self.next_patient_id += 1
            
        # Store the mapping.
        self.patient_id_map[str(original_id)] = new_id
        
        return new_id
    
    def get_modified_anonymization_profile(self):
        """Return an anonymization profile for the current settings."""
        # Start from the base profile.
        profile = get_anonymization_profile(self)
        
        # Adjust for the selected anonymization level.
        if self.anonymization_level == "partial":
            # Partial mode retains selected date and institution values.
            for key in ["StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
                       "StudyTime", "SeriesTime", "AcquisitionTime", "ContentTime",
                       "InstitutionName", "StationName"]:
                if key in profile:
                    del profile[key]
        
        # Adjust UID handling.
        if self.uid_handling == "generate":
            for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"]:
                if uid_tag in profile:
                    profile[uid_tag] = lambda x: generate_uid()
        
        return profile
    
    def _replace_uid_references(self, dataset):
        """Recursively replace mapped UI elements in a dataset."""
        replaced = 0
        for elem in dataset:
            if elem.VR == "SQ" and elem.value:
                for item in elem.value:
                    if item is not None:
                        replaced += self._replace_uid_references(item)
            elif elem.VR == "UI" and elem.value:
                old_uid = str(elem.value)
                if old_uid in self.uid_map:
                    elem.value = self.uid_map[old_uid]
                    replaced += 1
        return replaced
    
    def anonymize_dicom(self, dcm, anonymization_profile, remove_private_tags=True):
        """
        Anonymize a DICOM dataset.
        
        Args:
            dcm: DICOM dataset to anonymize.
            anonymization_profile: Active anonymization profile.
            remove_private_tags: Remove private tags when true.
            
        Returns:
            Mapping of changed attributes to before-and-after values.
        """
        self.log_message(f"Starting anonymization: {dcm.filename if hasattr(dcm, 'filename') else 'Unknown'}")
        changes = {}
        
        # Process private tags.
        if remove_private_tags:
            def remove_private_tags_recursive(dataset):
                count = 0
                private_tags = [tag for tag in dataset.keys() if tag.is_private]
                for tag in private_tags:
                    try:
                        del dataset[tag]
                        count += 1
                    except Exception as e:
                        self.logger.warning(f"Error removing private tag {tag}: {e}")
                
                # Recurse into sequence items.
                for elem in dataset.values():
                    if elem.VR == "SQ" and elem.value:
                        for item in elem.value:
                            if item is not None:
                                count += remove_private_tags_recursive(item)
                return count
            
            removed_count = remove_private_tags_recursive(dcm)
            self.log_message(f"Removed {removed_count} private tags")
        
        # Process attributes from the anonymization profile.
        processed_tags = 0
        for tag_name, replacement in anonymization_profile.items():
            # Process only attributes present in the dataset.
            if hasattr(dcm, tag_name):
                try:
                    original_value = getattr(dcm, tag_name)
                    
                    # Evaluate callable replacements; otherwise use the value.
                    if callable(replacement):
                        try:
                            new_value = replacement(original_value)
                        except Exception as e:
                            self.logger.warning(f"Error processing attribute {tag_name}: {e}")
                            continue
                    else:
                        new_value = replacement
                    
                    # Assign the replacement value.
                    try:
                        setattr(dcm, tag_name, new_value)
                        changes[tag_name] = {
                            "original_value": str(original_value),
                            "new_value": str(new_value)
                        }
                        processed_tags += 1
                    except Exception as e:
                        self.logger.warning(f"Error assigning attribute {tag_name}: {e}")
                except Exception as e:
                    self.logger.warning(f"Error processing attribute {tag_name}: {e}")
        
        self.log_message(f"Anonymized {processed_tags} attributes")
        return changes
    
    def process_directory(self, progress_callback=None):
        """
        Anonymize every readable DICOM file in the configured directory.
        """
        try:
            self.log_message("Starting processing...")
            
            # Resolve current settings.
            input_dir = self.input_dir
            output_dir = self.output_dir
            log_dir = self.log_dir
            keep_structure = self.keep_structure
            remove_private_tags = self.private_tags == "remove"
            
            # Verify the input directory.
            if not input_dir.exists():
                error_msg = f"Input directory does not exist: {input_dir}"
                self.log_message(error_msg)
                return
                
            self.log_message(f"Input directory: {input_dir}")
            self.log_message(f"Output directory: {output_dir}")
            self.log_message(f"Log directory: {log_dir}")
            
            # Create output and log directories when absent.
            output_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)
            
            # Reset UID and patient-ID mappings.
            self.uid_map = {}
            self.patient_id_map = {}
            self.patient_counter = 0
            
            # Build log and summary paths.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"rt_anonymization_log_{timestamp}.txt"
            summary_path = log_dir / f"rt_anonymization_summary_{timestamp}.json"
            
            # Add a file handler to the logger.
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Processing summary.
            summary = {
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processed_files": 0,
                "successful_files": 0,
                "skipped_files": 0,
                "error_files": 0,
                "file_details": [],
                "patient_id_map": {}
            }
            
            # Discover candidate files.
            dicom_files = find_dicom_files(input_dir)
            total_files = len(dicom_files)
            self.log_message(f"Search complete: found {total_files} files")
            
            if total_files == 0:
                self.log_message("No files were found for processing.")
                return
            
            # Resolve the anonymization profile.
            anonymization_profile = self.get_modified_anonymization_profile()
            self.log_message("Anonymization profile configured")
            
            # Pass 1: collect UID mappings.
            if self.uid_handling == "consistent":
                self.log_message("Pass 1: collecting UID mappings...")
                for i, file_path in enumerate(dicom_files):
                    try:
                        dcm_pass1 = pydicom.dcmread(str(file_path), force=True, stop_before_pixels=True)
                        for tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"]:
                            if hasattr(dcm_pass1, tag):
                                old_uid = str(getattr(dcm_pass1, tag))
                                if old_uid and old_uid not in self.uid_map:
                                    self.uid_map[old_uid] = generate_uid()
                    except pydicom.errors.InvalidDicomError:
                        pass
                    except Exception as e:
                        self.logger.warning(f"Pass 1 error for {file_path.name}: {str(e)}")
                self.log_message(f"Pass 1 complete: mapped {len(self.uid_map)} UIDs")
            
            # Pass 2: anonymize and save files.
            self.log_message("Pass 2: starting anonymization...")
            for i, file_path in enumerate(dicom_files):
                summary["processed_files"] += 1
                
                # Update progress.
                progress = (i + 1) / total_files * 100
                if self.root and hasattr(self, 'progress_var') and self.progress_var:
                    self.progress_var.set(progress)
                    self.status_var.set(f"Processing... {i+1}/{total_files} ({progress:.1f}%)")
                
                if progress_callback:
                    progress_callback(i + 1, total_files, file_path.name)
                
                self.log_message(f"Processing ({i+1}/{total_files}): {file_path.name}")
                
                try:
                    # Read the candidate as DICOM.
                    try:
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        
                        # Identify the file type.
                        modality = "Unknown"
                        file_type = "Unknown"
                        if hasattr(dcm, 'Modality'):
                            modality = dcm.Modality
                            if modality == "RTPLAN":
                                file_type = "Radiotherapy plan"
                            elif modality == "RTDOSE":
                                file_type = "Dose distribution"
                            elif modality == "RTSTRUCT":
                                file_type = "Structure contours"
                            elif modality == "CT" or modality == "RTIMAGE":
                                file_type = "CT image"
                        
                        self.log_message(f"File type: {file_type} (Modality: {modality})")
                        
                        # Build the output path.
                        if keep_structure:
                            # Preserve the source directory structure.
                            rel_path = file_path.relative_to(input_dir)
                            output_path = output_dir / rel_path
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                        else:
                            # Use a flat output directory.
                            output_path = output_dir / file_path.name
                        
                        # Record the patient-ID mapping.
                        if hasattr(dcm, 'PatientID') and dcm.PatientID:
                            original_id = dcm.PatientID
                            if original_id not in self.patient_id_map:
                                # Generate a new ID.
                                new_id = self.generate_anonymous_id(original_id)
                                
                                self.patient_id_map[original_id] = new_id
                                summary["patient_id_map"][original_id] = new_id
                                
                                # Mask part of the original ID in the log.
                                masked_id = self._mask_patient_id(original_id)
                                self.log_message(f"Patient ID mapping: {masked_id} -> {new_id}")
                        
                        # Anonymize and save the file.
                        self.log_message(f'Processing: {file_path.name} (type: {file_type})')
                        
                        # Anonymize the DICOM dataset.
                        changes = self.anonymize_dicom(dcm, anonymization_profile, remove_private_tags)
                        
                        # Recursively replace mapped UID references.
                        if self.uid_handling == "consistent":
                            replaced_refs = self._replace_uid_references(dcm)
                            self.log_message(f"Replaced {replaced_refs} UID references")
                        
                        # Save the anonymized DICOM.
                        try:
                            # Enforce value lengths for selected short strings.
                            for tag_name in ["StationName", "InstitutionName", "ReferringPhysicianName"]:
                                if hasattr(dcm, tag_name):
                                    value = getattr(dcm, tag_name)
                                    # SH values are limited to 16 characters.
                                    if len(str(value)) > 16:
                                        setattr(dcm, tag_name, str(value)[:16])
                                        self.logger.warning(f"Truncated overlong {tag_name}: {value} -> {str(value)[:16]}")
                            
                            # Repair known invalid values in UI elements.
                            for elem in dcm:
                                if elem.VR == "UI" and elem.value and not str(elem.value).startswith("1.2."):
                                    # Replace the known invalid MIM value.
                                    if str(elem.value) == "MIM":
                                        elem.value = generate_uid()
                                        self.logger.warning(f"Repaired invalid UI value: {elem.tag} MIM -> {elem.value}")
                            
                            # Ensure the output directory exists.
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Add standard file meta for non-standard input read
                            # with force=True.
                            if not hasattr(dcm, 'file_meta') or dcm.file_meta is None:
                                dcm.file_meta = FileMetaDataset()
                            if not hasattr(dcm.file_meta, 'MediaStorageSOPClassUID') and hasattr(dcm, 'SOPClassUID'):
                                dcm.file_meta.MediaStorageSOPClassUID = dcm.SOPClassUID
                            if not hasattr(dcm.file_meta, 'MediaStorageSOPInstanceUID') and hasattr(dcm, 'SOPInstanceUID'):
                                dcm.file_meta.MediaStorageSOPInstanceUID = dcm.SOPInstanceUID
                            if not hasattr(dcm.file_meta, 'TransferSyntaxUID') or not dcm.file_meta.TransferSyntaxUID:
                                dcm.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
                            
                            # Save with a standard DICM preamble and header.
                            dcm.save_as(str(output_path), write_like_original=False)
                            self.log_message(f"Saved anonymized file: {output_path.name}")
                        except Exception as save_error:
                            self.log_message(f"File-save error: {str(save_error)}")
                            raise save_error
                        
                        summary["file_details"].append({
                            "file_name": file_path.name,
                            "type": file_type,
                            "status": "success",
                            "changed_fields": changes
                        })
                        summary["successful_files"] += 1
                        
                    except pydicom.errors.InvalidDicomError:
                        error_msg = f'Skipped non-DICOM file: {file_path.name}'
                        self.log_message(error_msg)
                        summary["file_details"].append({
                            "file_name": file_path.name,
                            "type": "non-DICOM",
                            "status": "skipped"
                        })
                        summary["skipped_files"] += 1
                        
                except Exception as e:
                    error_msg = f'Processing error for {file_path.name}: {str(e)}'
                    self.log_message(error_msg)
                    self.logger.error(traceback.format_exc())
                    summary["file_details"].append({
                        "file_name": file_path.name,
                        "type": "error",
                        "status": "failed",
                        "error_details": str(e)
                    })
                    summary["error_files"] += 1
            
            # Record completion time.
            summary["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Write the JSON summary.
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.log_message("\nProcessing complete")
            self.log_message(f"Log file: {log_path}")
            self.log_message(f"Summary file: {summary_path}")
            
            if self.root and hasattr(self, 'status_var') and self.status_var:
                self.status_var.set(
                    f"Complete: {summary['successful_files']} succeeded, "
                    f"{summary['skipped_files']} skipped, {summary['error_files']} errors"
                )
            
            # Remove the temporary file handler.
            self.logger.removeHandler(file_handler)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            if self.root and hasattr(self, 'status_var') and self.status_var:
                self.status_var.set("An error occurred")
    
    def _mask_patient_id(self, patient_id):
        """Mask a patient ID for display."""
        id_str = str(patient_id)
        if len(id_str) > 4:
            return id_str[:2] + "***" + id_str[-2:]
        else:
            return "***"
