import os
import sys
import argparse
import pydicom
import hashlib
import uuid
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import logging
from pydicom.uid import generate_uid

class RTDicomAnonymizer:
    def __init__(self, root=None):
        self.root = root
    
        # Locate the program directory.
        script_dir = Path(__file__).parent.absolute()
    
        # Prefer default directories beside the program.
        self.input_dir = script_dir / 'input_dicom'
        self.output_dir = script_dir / 'anonymous_dicom'
        self.log_dir = script_dir / 'logs'
    
        # Create missing directories.
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
    
        # Anonymization profile.
        self.define_anonymization_profile()
    
        # Logger configuration.
        self.logger = self.setup_logger()
    
        if root:
            self.setup_gui()

        self.log_message("Anonymizer initialized")
        self.log_message(f"Initial input directory: {self.input_dir}")
        self.log_message(f"Initial output directory: {self.output_dir}")
        self.log_message(f"Initial log directory: {self.log_dir}")
    
    def setup_logger(self):
        """Configure the logger."""
        logger = logging.getLogger("RTDicomAnonymizer")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to prevent duplicates.
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Console handler.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def define_anonymization_profile(self):
        """Define the anonymization profile."""
        # Keys are DICOM keywords; values are replacements or callables.
        self.anonymization_profile = {
            # Basic patient information.
            "PatientName": "ANONYMOUS",
            "PatientID": lambda x: self.generate_anonymous_id(x),
            "PatientBirthDate": "19000101",
            "PatientSex": "O",  # Other
            "PatientAge": "000Y",
            "PatientWeight": "",
            "PatientAddress": "",
            "PatientTelephoneNumbers": "",

            # Study and institution information.
            "StudyID": lambda x: hashlib.md5(str(x).encode()).hexdigest()[:8],
            "AccessionNumber": "",
            "InstitutionName": "ANONYMOUS_INSTITUTION",
            "InstitutionAddress": "",
            "ReferringPhysicianName": "ANONYMOUS_PHYSICIAN",
            "PhysiciansOfRecord": "",
            "PerformingPhysicianName": "",
            "OperatorsName": "",

            # Identifiers.
            "StudyInstanceUID": lambda x: generate_uid(),
            "SeriesInstanceUID": lambda x: generate_uid(),
            "SOPInstanceUID": lambda x: generate_uid(),
            "FrameOfReferenceUID": lambda x: generate_uid(),

            # Dates and times.
            "StudyDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "SeriesDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "AcquisitionDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "ContentDate": lambda x: "2000" + str(x)[4:] if len(str(x)) == 8 else "20000101",
            "StudyTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "SeriesTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "AcquisitionTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            "ContentTime": lambda x: "000000.000" if len(str(x)) < 6 else str(x),
            
            # Other identifying information.
            "DeviceSerialNumber": "",
            "StationName": "ANONYMOUS_STATION",
            "ManufacturerModelName": "",
            
            # RT-specific attributes.
            "StructureSetLabel": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
            "StructureSetName": lambda x: f"ANONYMOUS_{str(x)[-5:]}",
            "ROIName": lambda x: f"ROI_{str(x)[-10:]}" if not any(organ in str(x).lower() for organ in ["lung", "heart", "liver", "kidney", "spinal", "brain"]) else str(x),
            "DoseComment": "ANONYMIZED",
            "PlanLabel": lambda x: f"ANONYMOUS_PLAN_{str(x)[-5:]}",
        }
    
    def generate_anonymous_id(self, original_id):
        """
        Generate a seven-digit anonymized patient ID beginning with 9.
        Reuse the same value for the same original ID.
        
        Args:
            original_id: Original patient ID.
            
        Returns:
            Seven-digit numeric ID beginning with 9.
        """
        # Use a mapping to preserve patient-ID consistency.
        if not hasattr(self, 'patient_id_map'):
            self.patient_id_map = {}
            
        # Reuse an existing mapping.
        if str(original_id) in self.patient_id_map:
            return self.patient_id_map[str(original_id)]
        
        # Generate the next sequential value starting at 9000001.
        if not hasattr(self, 'next_patient_id'):
            self.next_patient_id = 9000001
        else:
            self.next_patient_id += 1
            
        # Keep the value at or below 9999999.
        if self.next_patient_id > 9999999:
            # Fall back to six hash-derived digits if the sequence is exhausted.
            hash_id = int(hashlib.md5(str(original_id).encode()).hexdigest(), 16) % 1000000
            new_id = f"9{hash_id:06d}"
        else:
            new_id = str(self.next_patient_id)
            
        # Store the mapping.
        self.patient_id_map[str(original_id)] = new_id
        
        return new_id
    
    def setup_gui(self):
        """Create GUI components."""
        self.root.title("RT DICOM Anonymizer")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # Main frame.
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Directory settings.
        dir_frame = ttk.LabelFrame(main_frame, text="Directories", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # Input directory.
        ttk.Label(dir_frame, text="Input directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=str(self.input_dir))
        ttk.Entry(dir_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_input_dir).grid(row=0, column=2, pady=5)

        # Output directory.
        ttk.Label(dir_frame, text="Output directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_output_dir).grid(row=1, column=2, pady=5)

        # Log directory.
        ttk.Label(dir_frame, text="Log directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_dir_var = tk.StringVar(value=str(self.log_dir))
        ttk.Entry(dir_frame, textvariable=self.log_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_log_dir).grid(row=2, column=2, pady=5)
        
        # Anonymization settings.
        settings_frame = ttk.LabelFrame(main_frame, text="Anonymization settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Select the anonymization level.
        ttk.Label(settings_frame, text="Anonymization level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        ttk.Radiobutton(settings_frame, text="Full", variable=self.anonymization_level,
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Partial (retain dates and institution)", variable=self.anonymization_level,
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Private-tag handling.
        ttk.Label(settings_frame, text="Private tags:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.private_tags = tk.StringVar(value="remove")
        ttk.Radiobutton(settings_frame, text="Remove all", variable=self.private_tags,
                       value="remove").grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Keep", variable=self.private_tags,
                       value="keep").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # UID handling.
        ttk.Label(settings_frame, text="UID handling:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.uid_handling = tk.StringVar(value="consistent")
        ttk.Radiobutton(settings_frame, text="Preserve consistency", variable=self.uid_handling,
                       value="consistent").grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Generate all", variable=self.uid_handling,
                       value="generate").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # Directory-structure preservation.
        ttk.Label(settings_frame, text="Directory structure:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.keep_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Preserve original structure",
                        variable=self.keep_structure).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Patient-ID transformation.
        ttk.Label(settings_frame, text="Patient ID method:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.patient_id_method = tk.StringVar(value="hash")
        ttk.Radiobutton(settings_frame, text="Hash", variable=self.patient_id_method,
                       value="hash").grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Sequential (for example Patient_001)", variable=self.patient_id_method,
                       value="sequential").grid(row=4, column=2, sticky=tk.W, pady=5)
        
        # Action buttons.
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Run anonymization", command=self.start_processing).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Inspect directory", command=self.check_directory).pack(side=tk.RIGHT, padx=5)
        
        # Progress display.
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Progress bar.
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Log text area.
        self.log_text = tk.Text(progress_frame, height=15, width=70, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar.
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar.
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_directory(self):
        """Inspect the selected directory."""
        if not self.input_dir_var.get():
            messagebox.showerror("Error", "Select an input directory.")
            return
            
        input_dir = Path(self.input_dir_var.get())
        if not input_dir.exists():
            messagebox.showerror("Error", "The input directory does not exist.")
            return
            
        self.log_message(f"Inspecting directory '{input_dir}'...")
        
        # List files in the directory.
        file_count = 0
        dicom_count = 0
        
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = Path(root) / file
                file_count += 1
                
                try:
                    # Check whether the file is readable as DICOM.
                    dcm = pydicom.dcmread(str(file_path), force=False)
                    dicom_count += 1
                    
                    # Display Modality when available.
                    modality = "Unknown"
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                    
                    # Display a masked Patient ID when available.
                    patient_id = "Unknown"
                    if hasattr(dcm, 'PatientID') and dcm.PatientID:
                        id_str = str(dcm.PatientID)
                        if len(id_str) > 4:
                            patient_id = id_str[:2] + "***" + id_str[-2:]
                        else:
                            patient_id = "***"
                    
                    self.log_message(f"DICOM: {file_path.name}, Modality: {modality}, Patient ID: {patient_id}")
                    
                except:
                    pass
        
        self.log_message(f"Inspection complete: {file_count} total files, {dicom_count} DICOM files")
        
        if dicom_count == 0:
            self.log_message("Warning: no DICOM files were found.")
            messagebox.showwarning("Warning", "No DICOM files were found in the input directory.")
    
    def browse_input_dir(self):
        """Select an input directory."""
        directory = filedialog.askdirectory(title="Select a directory containing DICOM files")
        if directory:
            self.input_dir_var.set(directory)
            self.log_message(f"Input directory set: {directory}")
    
    def browse_output_dir(self):
        """Select an output directory."""
        directory = filedialog.askdirectory(title="Select the anonymized-output directory")
        if directory:
            self.output_dir_var.set(directory)
            self.log_message(f"Output directory set: {directory}")
    
    def browse_log_dir(self):
        """Select a log directory."""
        directory = filedialog.askdirectory(title="Select the log directory")
        if directory:
            self.log_dir_var.set(directory)
            self.log_message(f"Log directory set: {directory}")
    
    def log_message(self, message):
        """Display a log message."""
        try:
            if self.root:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            
            # Always write through the configured logger.
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"Logging error: {str(e)}")
    
    def get_modified_anonymization_profile(self):
        """
        Adjust the anonymization profile from current GUI settings.
        """
        profile = self.anonymization_profile.copy()
        
        # Read settings from the active GUI.
        if self.root:
            # Adjust for the anonymization level.
            if self.anonymization_level.get() == "partial":
                # Partial mode retains selected dates and institution values.
                for key in ["StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
                          "StudyTime", "SeriesTime", "AcquisitionTime", "ContentTime",
                          "InstitutionName", "StationName"]:
                    if key in profile:
                        del profile[key]
            
            # UID handling.
            if self.uid_handling.get() == "consistent":
                # Generate deterministic hash-based UIDs for consistency.
                uid_map = {}
                for uid_tag in ["StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID"]:
                    if uid_tag in profile:
                        profile[uid_tag] = lambda x, tag=uid_tag: uid_map.setdefault(
                            f"{tag}_{x}", generate_uid())
            
            # Patient-ID transformation.
            if self.patient_id_method.get() == "sequential":
                # Manage patient IDs sequentially.
                self.patient_counter = 0
                def sequential_id(x):
                    self.patient_counter += 1
                    return f"Patient_{self.patient_counter:03d}"
                profile["PatientID"] = sequential_id
        
        return profile

    def anonymize_dicom(self, dcm, anonymization_profile, remove_private_tags=True):
        """
        Anonymize a DICOM dataset.
        
        Args:
            dcm: DICOM dataset to anonymize.
            anonymization_profile: Active profile.
            remove_private_tags: Remove private tags when true.
            
        Returns:
            Mapping of changed attributes to before-and-after values.
        """
        self.log_message(f"Starting anonymization: {dcm.filename if hasattr(dcm, 'filename') else 'Unknown'}")
        changes = {}
        
        # Process private tags.
        if remove_private_tags:
            private_tags = [tag for tag in dcm.keys() if tag.is_private]
            for tag in private_tags:
                if tag in dcm:
                    del dcm[tag]
            
            self.log_message(f"Removed {len(private_tags)} private tags")
        
        # Process configured attributes.
        processed_tags = 0
        for tag_name, replacement in anonymization_profile.items():
            # Process only present attributes.
            if hasattr(dcm, tag_name):
                try:
                    original_value = getattr(dcm, tag_name)
                    
                    # Evaluate callable replacements or use the value directly.
                    if callable(replacement):
                        try:
                            new_value = replacement(original_value)
                        except Exception as e:
                            self.logger.warning(f"Error processing attribute {tag_name}: {e}")
                            continue
                    else:
                        new_value = replacement
                    
                    # Assign the replacement.
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
    
    def process_directory(self):
        """
        Anonymize DICOM files in the selected directory and record changes.
        """
        try:
            self.log_message("Starting processing...")
            
            # Resolve input and output paths.
            if self.root:
                input_dir = Path(self.input_dir_var.get())
                output_dir = Path(self.output_dir_var.get())
                log_dir = Path(self.log_dir_var.get())
                keep_structure = self.keep_structure.get()
                remove_private_tags = self.private_tags.get() == "remove"
                
                # Verify that the input directory exists.
                if not input_dir.exists():
                    error_msg = f"Input directory does not exist: {input_dir}"
                    self.log_message(error_msg)
                    messagebox.showerror("Error", error_msg)
                    return
                    
                self.log_message(f"Input directory: {input_dir}")
                self.log_message(f"Output directory: {output_dir}")
                self.log_message(f"Log directory: {log_dir}")
            else:
                input_dir = Path('input_dicom')
                output_dir = Path('anonymous_dicom')
                log_dir = Path('logs')
                keep_structure = True
                remove_private_tags = True
            
            # Create output and log directories when absent.
            output_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)
            
            self.log_message(f"Output directory ready: {output_dir}")
            self.log_message(f"Log directory ready: {log_dir}")
            
            # Reset UID mappings.
            self.uid_map = {}
            
            # Reset patient-ID mappings.
            self.patient_id_map = {}
            self.patient_counter = 0
            
            # Build log and summary paths.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"rt_anonymization_log_{timestamp}.txt"
            summary_path = log_dir / f"rt_anonymization_summary_{timestamp}.json"
            
            self.log_message(f"Log file: {log_path}")
            self.log_message(f"Summary file: {summary_path}")
            
            # Add a file handler.
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
            
            # Discover candidate files recursively.
            self.log_message("Searching for files...")
            dicom_files = []
            for root, _, files in os.walk(input_dir):
                for file in files:
                    file_path = Path(root) / file
                    dicom_files.append(file_path)
            
            total_files = len(dicom_files)
            self.log_message(f"Search complete: found {total_files} files")
            
            if total_files == 0:
                self.log_message("No files were found for processing.")
                if self.root:
                    self.status_var.set("No files found")
                    messagebox.showinfo("Information", "No files were found in the input directory.")
                return
            
            # Resolve the anonymization profile.
            anonymization_profile = self.get_modified_anonymization_profile()
            self.log_message("Anonymization profile configured")
            
            # Process files from the input directory.
            for i, file_path in enumerate(dicom_files):
                if file_path.is_file():
                    summary["processed_files"] += 1
                    
                    # Update progress.
                    progress = (i + 1) / total_files * 100
                    if self.root:
                        self.progress_var.set(progress)
                        self.status_var.set(f"Processing... {i+1}/{total_files} ({progress:.1f}%)")
                    
                    self.log_message(f"Processing ({i+1}/{total_files}): {file_path.name}")
                    
                    try:
                        # Check whether the file is DICOM.
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
                                # Preserve source directory structure.
                                rel_path = file_path.relative_to(input_dir)
                                output_path = output_dir / rel_path
                                output_path.parent.mkdir(parents=True, exist_ok=True)
                            else:
                                # Use a flat output directory.
                                output_path = output_dir / file_path.name
                            
                            self.log_message(f"Output: {output_path}")
                            
                            # Record a patient-ID mapping when available.
                            if hasattr(dcm, 'PatientID') and dcm.PatientID:
                                original_id = dcm.PatientID
                                if original_id not in self.patient_id_map:
                                    # Generate a seven-digit value beginning with 9.
                                    new_id = self.generate_anonymous_id(original_id)
                                    
                                    self.patient_id_map[original_id] = new_id
                                    summary["patient_id_map"][original_id] = new_id
                                    
                                    # Mask part of the original ID in the log.
                                    if len(str(original_id)) > 4:
                                        masked_id = str(original_id)[:2] + "***" + str(original_id)[-2:]
                                    else:
                                        masked_id = "***"
                                    
                                    self.log_message(f"Patient ID mapping: {masked_id} -> {new_id}")
                                
                                # Use generate_anonymous_id for profile mapping.
                                anonymization_profile["PatientID"] = lambda x: self.generate_anonymous_id(str(x))
                            
                            # Anonymize and save the file.
                            msg = f'Processing: {file_path.name} (type: {file_type})'
                            self.log_message(msg)
                            
                            # Anonymize the DICOM dataset.
                            changes = self.anonymize_dicom(dcm, anonymization_profile, remove_private_tags)
                            
                            # Save the anonymized dataset.
                            try:
                                dcm.save_as(str(output_path))
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
            
            msg = "\nProcessing complete"
            self.log_message(msg)
            msg = f"Log file: {log_path}"
            self.log_message(msg)
            msg = f"Summary file: {summary_path}"
            self.log_message(msg)
            
            if self.root:
                self.status_var.set(
                    f"Complete: {summary['successful_files']} succeeded, "
                    f"{summary['skipped_files']} skipped, {summary['error_files']} errors"
                )
                messagebox.showinfo("Processing complete",
                               "Processing completed.\n\n"
                               f"Succeeded: {summary['successful_files']}\n"
                               f"Skipped: {summary['skipped_files']}\n"
                               f"Errors: {summary['error_files']}\n\n"
                               f"Log file: {log_path}")

            # Remove the temporary file handler.
            self.logger.removeHandler(file_handler)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            if self.root:
                self.status_var.set("An error occurred")
                messagebox.showerror("Error", error_msg)

    def start_processing(self):
        """Start processing on a worker thread."""
        # Do not start while another run is active.
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            messagebox.showwarning("Warning", "Processing is already running.")
            return
        
        # Validate directories.
        if not self.input_dir_var.get():
            messagebox.showerror("Error", "Select an input directory.")
            return
        
        if not self.output_dir_var.get():
            messagebox.showerror("Error", "Select an output directory.")
            return
        
        if not self.log_dir_var.get():
            messagebox.showerror("Error", "Select a log directory.")
            return
        
        # Clear previous logs.
        self.log_text.delete(1.0, tk.END)
        
        # Start processing.
        self.status_var.set("Starting processing...")
        self.progress_var.set(0)
        self.log_message("Starting worker thread...")
        
        # Run in the background.
        self.process_thread = threading.Thread(target=self.process_directory)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # Report whether the worker started.
        self.log_message(f"Worker status: {'running' if self.process_thread.is_alive() else 'failed to start'}")


def main():
    """Run the legacy anonymizer script."""
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(description='RT DICOM anonymizer')
    parser.add_argument('--nogui', action='store_true', help='Run without the GUI')
    parser.add_argument('--input', help='Input directory path')
    parser.add_argument('--output', help='Output directory path')
    parser.add_argument('--log', help='Log directory path')
    args = parser.parse_args()
    
    if args.nogui:
        # Command-line mode.
        print("Running in command-line mode...")
        anonymizer = RTDicomAnonymizer()
        
        # Apply provided arguments.
        if args.input:
            anonymizer.input_dir = Path(args.input)
        if args.output:
            anonymizer.output_dir = Path(args.output)
        if args.log:
            anonymizer.log_dir = Path(args.log)
            
        anonymizer.process_directory()
    else:
        # GUI mode.
        print("Running in GUI mode...")
        root = tk.Tk()
        app = RTDicomAnonymizer(root)
        root.mainloop()

if __name__ == '__main__':
    print("Starting program...")
    main()
