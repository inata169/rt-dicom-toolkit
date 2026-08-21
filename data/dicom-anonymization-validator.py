import os
import sys
import argparse
import pydicom
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import traceback
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import re

class RTDicomValidator:
    def __init__(self, root=None):
        self.root = root
    
        # Resolve paths relative to this script.
        script_dir = Path(__file__).parent.absolute()
    
        # Default directories
        self.original_dir = script_dir / 'input_dicom'
        self.anonymized_dir = script_dir / 'anonymous_dicom'
        self.report_dir = script_dir / 'validation_reports'
    
        # Create the report directory when needed.
        self.report_dir.mkdir(exist_ok=True)
    
        # Logging
        self.logger = self.setup_logger()
    
        # Validation rules
        self.define_validation_rules()
    
        if root:
            self.setup_gui()
            self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.log_message("Anonymization validator initialized")
        self.log_message(f"Default original directory: {self.original_dir}")
        self.log_message(f"Default anonymized directory: {self.anonymized_dir}")
        self.log_message(f"Default report directory: {self.report_dir}")

    def close(self):
        """Close the Tk event loop and destroy the window."""
        self.root.quit()
        self.root.destroy()
    
    def setup_logger(self):
        """Configure and return the application logger."""
        logger = logging.getLogger("RTDicomValidator")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicate output.
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def define_validation_rules(self):
        """Define the DICOM tag validation rules."""
        # Tags that must be anonymized
        self.must_anonymize_tags = [
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientAddress",
            "PatientTelephoneNumbers",
            "ReferringPhysicianName",
            "PhysiciansOfRecord",
            "PerformingPhysicianName",
            "InstitutionName",
            "InstitutionAddress",
            "StationName",
            "OperatorsName"
        ]
        
        # UID tags
        self.uid_tags = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID"
        ]
        
        # Tags whose structural values must be preserved
        self.structure_tags = [
            "Modality",
            "SOPClassUID",
            "ImageType",
            "SamplesPerPixel",
            "PhotometricInterpretation",
            "BitsAllocated",
            "BitsStored",
            "HighBit",
            "PixelRepresentation",
            "NumberOfFrames"
        ]
        
        # Tags whose anonymization depends on the selected level
        self.optional_anonymize_tags = [
            "StudyDate",
            "SeriesDate",
            "AcquisitionDate",
            "ContentDate",
            "StudyTime",
            "SeriesTime",
            "AcquisitionTime",
            "ContentTime",
            "AccessionNumber",
            "StudyID",
            "SeriesNumber",
            "AcquisitionNumber",
            "InstanceNumber",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "DeviceSerialNumber"
        ]
        
        # RT-specific tags
        self.rt_specific_tags = [
            "StructureSetLabel",
            "StructureSetName",
            "ROIName",
            "DoseComment",
            "PlanLabel"
        ]

    def setup_gui(self):
        """Build the graphical user interface."""
        self.root.title("RT DICOM Anonymization Validator")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Directory selection
        dir_frame = ttk.LabelFrame(main_frame, text="Directories", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # Original directory
        ttk.Label(dir_frame, text="Original directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.original_dir_var = tk.StringVar(value=str(self.original_dir))
        ttk.Entry(dir_frame, textvariable=self.original_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_original_dir).grid(row=0, column=2, pady=5)
        
        # Anonymized directory
        ttk.Label(dir_frame, text="Anonymized directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.anonymized_dir_var = tk.StringVar(value=str(self.anonymized_dir))
        ttk.Entry(dir_frame, textvariable=self.anonymized_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_anonymized_dir).grid(row=1, column=2, pady=5)
        
        # Report directory
        ttk.Label(dir_frame, text="Report directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.report_dir_var = tk.StringVar(value=str(self.report_dir))
        ttk.Entry(dir_frame, textvariable=self.report_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_report_dir).grid(row=2, column=2, pady=5)
        
        # Validation settings
        settings_frame = ttk.LabelFrame(main_frame, text="Validation Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Anonymization level
        ttk.Label(settings_frame, text="Anonymization level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        ttk.Radiobutton(settings_frame, text="Full anonymization", variable=self.anonymization_level,
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Partial anonymization (preserve dates and institution data)", variable=self.anonymization_level,
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Private tags
        ttk.Label(settings_frame, text="Private tags:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.check_private_tags = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Verify that private tags are removed",
                        variable=self.check_private_tags).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # File structure
        ttk.Label(settings_frame, text="Structure:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.check_file_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Verify that file structure is preserved",
                       variable=self.check_file_structure).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # UIDs
        ttk.Label(settings_frame, text="UIDs:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.check_uid_changed = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Verify that all UIDs are changed",
                        variable=self.check_uid_changed).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Detailed report
        ttk.Label(settings_frame, text="Report level:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.detailed_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Generate a detailed report",
                        variable=self.detailed_report).grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Run Validation", command=self.start_validation).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Compare Directories", command=self.compare_directories).pack(side=tk.RIGHT, padx=5)
        
        # Tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        
        # Log text area
        self.log_text = tk.Text(log_frame, height=15, width=70, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        
        # Summary text area
        self.summary_text = tk.Text(summary_frame, height=15, width=70, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        summary_scrollbar = ttk.Scrollbar(self.summary_text, command=self.summary_text.yview)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.config(yscrollcommand=summary_scrollbar.set)
        
        # Graph tab
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Graphs")
        
        # Graph canvas
        # Construct an unmanaged Figure so Matplotlib does not create a hidden
        # Tk root that would keep Python alive after this window is closed.
        self.figure = Figure(figsize=(8, 6))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Details tab
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Details")
        
        # Details tree
        self.tree = ttk.Treeview(details_frame)
        self.tree["columns"] = ("Original", "Anonymized", "Status")
        self.tree.column("#0", width=200, minwidth=200)
        self.tree.column("Original", width=200, minwidth=200)
        self.tree.column("Anonymized", width=200, minwidth=200)
        self.tree.column("Status", width=100, minwidth=100)
        
        self.tree.heading("#0", text="Tag")
        self.tree.heading("Original", text="Original")
        self.tree.heading("Anonymized", text="Anonymized")
        self.tree.heading("Status", text="Status")
        
        # Tree scrollbar
        tree_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Layout
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_original_dir(self):
        """Select the directory containing original DICOM files."""
        directory = filedialog.askdirectory(title="Select the original DICOM directory")
        if directory:
            self.original_dir_var.set(directory)
            self.log_message(f"Original directory set: {directory}")
    
    def browse_anonymized_dir(self):
        """Select the directory containing anonymized DICOM files."""
        directory = filedialog.askdirectory(title="Select the anonymized DICOM directory")
        if directory:
            self.anonymized_dir_var.set(directory)
            self.log_message(f"Anonymized directory set: {directory}")
    
    def browse_report_dir(self):
        """Select the report output directory."""
        directory = filedialog.askdirectory(title="Select the validation report directory")
        if directory:
            self.report_dir_var.set(directory)
            self.log_message(f"Report directory set: {directory}")
    
    def log_message(self, message):
        """Write a message to the GUI, console, and logger."""
        try:
            if self.root:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            
            # Always write to the console as well.
            print(message)
            self.logger.info(message)
        except Exception as e:
            print(f"Log output error: {str(e)}")
            
    def update_summary(self, message):
        """Append text to the summary pane."""
        try:
            if self.root:
                self.summary_text.insert(tk.END, message + "\n")
                self.summary_text.see(tk.END)
                self.root.update_idletasks()
        except Exception as e:
            print(f"Summary update error: {str(e)}")
    
    def compare_directories(self):
        """Compare the basic contents of the selected directories."""
        try:
            if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
                messagebox.showerror("Error", "Select both the original and anonymized directories.")
                return
                
            original_dir = Path(self.original_dir_var.get())
            anonymized_dir = Path(self.anonymized_dir_var.get())
            
            if not original_dir.exists() or not anonymized_dir.exists():
                messagebox.showerror("Error", "One or more selected directories do not exist.")
                return
                
            self.log_message(f"Comparing directories: {original_dir} and {anonymized_dir}")
            
            # Count readable DICOM files.
            original_files = []
            anonymized_files = []
            
            for root, _, files in os.walk(original_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # Confirm that the file can be read as DICOM.
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        # Require SOPClassUID as a basic DICOM check.
                        if hasattr(dcm, 'SOPClassUID'):
                            original_files.append(file_path)
                    except:
                        pass
            
            for root, _, files in os.walk(anonymized_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # Confirm that the file can be read as DICOM.
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        # Require SOPClassUID as a basic DICOM check.
                        if hasattr(dcm, 'SOPClassUID'):
                            anonymized_files.append(file_path)
                    except:
                        pass
            
            # Write results to the log and summary.
            self.log_message(f"DICOM files in original directory: {len(original_files)}")
            self.log_message(f"DICOM files in anonymized directory: {len(anonymized_files)}")
            
            self.summary_text.delete(1.0, tk.END)
            self.update_summary("=== Directory Comparison ===")
            self.update_summary(f"Original directory: {original_dir}")
            self.update_summary(f"Anonymized directory: {anonymized_dir}")
            self.update_summary(f"Original DICOM files: {len(original_files)}")
            self.update_summary(f"Anonymized DICOM files: {len(anonymized_files)}")
            
            if len(original_files) == len(anonymized_files):
                self.update_summary("\n✅ File counts match.")
            else:
                self.update_summary("\n⚠️ File counts do not match.")
                if len(original_files) > len(anonymized_files):
                    self.update_summary(f"  Missing anonymized files: {len(original_files) - len(anonymized_files)}")
                else:
                    self.update_summary(f"  Extra anonymized files: {len(anonymized_files) - len(original_files)}")
            
            # Collect modality distributions.
            original_modalities = {}
            anonymized_modalities = {}
            
            for file_path in original_files:
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True)
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                        if modality in original_modalities:
                            original_modalities[modality] += 1
                        else:
                            original_modalities[modality] = 1
                except:
                    pass
            
            for file_path in anonymized_files:
                try:
                    dcm = pydicom.dcmread(str(file_path), force=True)
                    if hasattr(dcm, 'Modality'):
                        modality = dcm.Modality
                        if modality in anonymized_modalities:
                            anonymized_modalities[modality] += 1
                        else:
                            anonymized_modalities[modality] = 1
                except:
                    pass
            
            # Plot modality distributions.
            self.ax.clear()
            
            # Prepare plot data.
            modalities = list(set(list(original_modalities.keys()) + list(anonymized_modalities.keys())))
            original_counts = [original_modalities.get(m, 0) for m in modalities]
            anonymized_counts = [anonymized_modalities.get(m, 0) for m in modalities]
            
            # Draw the graph.
            x = np.arange(len(modalities))
            width = 0.35
            
            self.ax.bar(x - width/2, original_counts, width, label='Original')
            self.ax.bar(x + width/2, anonymized_counts, width, label='Anonymized')
            
            self.ax.set_title('Modality Distribution Comparison')
            self.ax.set_xlabel('Modality')
            self.ax.set_ylabel('File Count')
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(modalities)
            self.ax.legend()
            
            self.canvas.draw()
            
            # Add modality distributions to the summary.
            self.update_summary("\n=== Modality Distribution ===")
            for modality in modalities:
                orig_count = original_modalities.get(modality, 0)
                anon_count = anonymized_modalities.get(modality, 0)
                status = "✅" if orig_count == anon_count else "⚠️"
                self.update_summary(f"{status} {modality}: original {orig_count}, anonymized {anon_count}")
            
            # Update the details tree.
            self.tree.delete(*self.tree.get_children())
            
            # Create one group per tag category.
            must_anonymize_group = self.tree.insert("", "end", text="Required Anonymization", open=True)
            uid_group = self.tree.insert("", "end", text="UIDs", open=True)
            structure_group = self.tree.insert("", "end", text="Structure", open=True)
            optional_group = self.tree.insert("", "end", text="Optional Anonymization", open=True)
            rt_group = self.tree.insert("", "end", text="RT-Specific Attributes", open=True)
            
            # Directory comparison has no per-file values.
            for tag in self.must_anonymize_tags:
                self.tree.insert(must_anonymize_group, "end", text=tag, values=("(shown during file validation)", "(shown during file validation)", "-"))
            
            for tag in self.uid_tags:
                self.tree.insert(uid_group, "end", text=tag, values=("(shown during file validation)", "(shown during file validation)", "-"))
            
            for tag in self.structure_tags:
                self.tree.insert(structure_group, "end", text=tag, values=("(shown during file validation)", "(shown during file validation)", "-"))
            
            for tag in self.optional_anonymize_tags:
                self.tree.insert(optional_group, "end", text=tag, values=("(shown during file validation)", "(shown during file validation)", "-"))
            
            for tag in self.rt_specific_tags:
                self.tree.insert(rt_group, "end", text=tag, values=("(shown during file validation)", "(shown during file validation)", "-"))
            
            # Show the details tab.
            self.notebook.select(3)
            
        except Exception as e:
            error_msg = f"Directory comparison failed: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def compare_dicom_files(self, original_file, anonymized_file):
        """Compare two DICOM files and evaluate anonymization."""
        try:
            # Read both files.
            original_dcm = pydicom.dcmread(str(original_file), force=True)
            anonymized_dcm = pydicom.dcmread(str(anonymized_file), force=True)
            
            results = {
                "must_anonymize": {},  # Required anonymization results
                "uid_tags": {},        # UID results
                "structure_tags": {},  # Structure preservation results
                "optional_tags": {},   # Optional anonymization results
                "rt_specific_tags": {}, # RT-specific results
                "private_tags": {      # Private-tag results
                    "original_count": 0,
                    "anonymized_count": 0
                },
                "pixel_data": {        # Pixel-data comparison
                    "original_shape": None,
                    "anonymized_shape": None,
                    "match": False
                }
            }
            
            # Check required anonymization tags.
            for tag in self.must_anonymize_tags:
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
            
            # Check UIDs.
            for tag in self.uid_tags:
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
            
            # Check structural attributes.
            for tag in self.structure_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Structural values should be preserved.
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
            
            # Check optional anonymization tags.
            for tag in self.optional_anonymize_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # Apply the selected anonymization level.
                if self.anonymization_level.get() == "full":
                    # Full anonymization requires a change.
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
                    # Partial anonymization may preserve the value.
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
            for tag in self.rt_specific_tags:
                original_value = getattr(original_dcm, tag, "N/A") if hasattr(original_dcm, tag) else "N/A"
                anonymized_value = getattr(anonymized_dcm, tag, "N/A") if hasattr(anonymized_dcm, tag) else "N/A"
                
                # ROIName needs special handling because anatomy names may be preserved.
                if tag == "ROIName":
                    status = "special handling"
                    # Common anatomy names such as heart and lung should be preserved.
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
                    # Other RT-specific attributes should be anonymized.
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
            
            # Compare pixel data when present in both files.
            if hasattr(original_dcm, 'PixelData') and hasattr(anonymized_dcm, 'PixelData'):
                try:
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
                    self.logger.warning(f"Pixel-data comparison failed: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"DICOM comparison failed: {e}")
            self.logger.error(traceback.format_exc())
            return None
            
    def validate_files(self, original_dir, anonymized_dir):
        """Validate DICOM files in the two directories."""
        try:
            # Collect original DICOM files.
            original_files = []
            for root, _, files in os.walk(original_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # Confirm that this is a readable DICOM file.
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        if hasattr(dcm, 'SOPClassUID'):
                            original_files.append(file_path)
                    except:
                        pass
            
            # Collect anonymized DICOM files.
            anonymized_files = []
            for root, _, files in os.walk(anonymized_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        # Confirm that this is a readable DICOM file.
                        dcm = pydicom.dcmread(str(file_path), force=True)
                        if hasattr(dcm, 'SOPClassUID'):
                            anonymized_files.append(file_path)
                    except:
                        pass
            
            self.log_message(f"Original DICOM files: {len(original_files)}")
            self.log_message(f"Anonymized DICOM files: {len(anonymized_files)}")
            
            # Aggregate statistics
            summary = {
                "total_files": len(original_files),
                "matched_files": 0,
                "must_anonymize_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.must_anonymize_tags},
                "uid_stats": {tag: {"changed": 0, "not_changed": 0} for tag in self.uid_tags},
                "structure_stats": {tag: {"preserved": 0, "not_preserved": 0} for tag in self.structure_tags},
                "private_tags_stats": {"removed": 0, "not_removed": 0},
                "modality_stats": {},
                "rt_specific_stats": {tag: {"anonymized": 0, "not_anonymized": 0} for tag in self.rt_specific_tags},
                "patient_id_map": {},
            }
            
            # Per-file results
            detailed_results = []
            
            # Match and validate original/anonymized pairs.
            progress_count = 0
            
            # Match by relative path. Other datasets may need modality and series metadata.
            original_files_map = {}
            
            # Index original files by relative path.
            for file_path in original_files:
                rel_path = file_path.relative_to(original_dir)
                original_files_map[str(rel_path)] = file_path
            
            # Match and validate each anonymized file.
            for anon_file in anonymized_files:
                progress_count += 1
                
                # Update progress.
                if self.root:
                    progress = progress_count / len(anonymized_files) * 100
                    self.status_var.set(f"Validating... {progress_count}/{len(anonymized_files)} ({progress:.1f}%)")
                
                try:
                    # Match by relative path.
                    rel_path = anon_file.relative_to(anonymized_dir)
                    
                    # Find the matching original file.
                    if str(rel_path) in original_files_map:
                        orig_file = original_files_map[str(rel_path)]
                        
                        self.log_message(f"Validating: {rel_path}")
                        
                        # Compare the pair.
                        results = self.compare_dicom_files(orig_file, anon_file)
                        
                        if results:
                            summary["matched_files"] += 1
                            
                            # Update modality statistics.
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
                            
                            # Required anonymization statistics
                            for tag, info in results["must_anonymize"].items():
                                if info["anonymized"]:
                                    summary["must_anonymize_stats"][tag]["anonymized"] += 1
                                else:
                                    summary["must_anonymize_stats"][tag]["not_anonymized"] += 1
                            
                            # UID statistics
                            for tag, info in results["uid_tags"].items():
                                if info["changed"]:
                                    summary["uid_stats"][tag]["changed"] += 1
                                else:
                                    summary["uid_stats"][tag]["not_changed"] += 1
                            
                            # Structure preservation statistics
                            for tag, info in results["structure_tags"].items():
                                if info["preserved"]:
                                    summary["structure_stats"][tag]["preserved"] += 1
                                else:
                                    summary["structure_stats"][tag]["not_preserved"] += 1
                            
                            # Private-tag statistics
                            if results["private_tags"]["anonymized_count"] == 0:
                                summary["private_tags_stats"]["removed"] += 1
                            else:
                                summary["private_tags_stats"]["not_removed"] += 1
                            
                            # Update the patient-ID mapping.
                            if "PatientID" in results["must_anonymize"]:
                                orig_id = results["must_anonymize"]["PatientID"]["original"]
                                anon_id = results["must_anonymize"]["PatientID"]["anonymized"]
                                
                                if orig_id != "N/A" and anon_id != "N/A":
                                    summary["patient_id_map"][orig_id] = anon_id
                            
                            # Store detailed results.
                            if self.detailed_report.get():
                                detailed_results.append({
                                    "original_file": str(orig_file),
                                    "anonymized_file": str(anon_file),
                                    "results": results
                                })
                            
                            # Show the latest file result in the details tree.
                            if self.root:
                                self.update_treeview(results)
                    else:
                        self.log_message(f"No matching original file: {rel_path}")
                
                except Exception as e:
                    self.log_message(f"File validation error: {str(e)}")
                    self.logger.error(traceback.format_exc())
            
            # Generate the summary report.
            report = self.generate_summary_report(summary)
            
            # Save the detailed report.
            if self.detailed_report.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                detailed_report_path = Path(self.report_dir_var.get()) / f"detailed_validation_report_{timestamp}.json"
                
                with open(detailed_report_path, 'w', encoding='utf-8') as f:
                    json.dump(detailed_results, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"Detailed report saved: {detailed_report_path}")
            
            # Draw validation graphs.
            self.draw_validation_graphs(summary)
            
            return report
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            return None
    
    def update_treeview(self, results):
        """Update the details tree with validation results."""
        try:
            self.tree.delete(*self.tree.get_children())
            
            # Create one group per tag category.
            must_anonymize_group = self.tree.insert("", "end", text="Required Anonymization", open=True)
            uid_group = self.tree.insert("", "end", text="UIDs", open=True)
            structure_group = self.tree.insert("", "end", text="Structure", open=True)
            optional_group = self.tree.insert("", "end", text="Optional Anonymization", open=True)
            rt_group = self.tree.insert("", "end", text="RT-Specific Attributes", open=True)
            
            # Required anonymization tags
            for tag, info in results["must_anonymize"].items():
                # Truncate long original values.
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                # Truncate long anonymized values.
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                # Add a status icon.
                status = info["status"]
                if info["anonymized"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(must_anonymize_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # UIDs
            for tag, info in results["uid_tags"].items():
                # UIDs are truncated for display.
                orig_value = info["original"]
                if len(orig_value) > 20:
                    orig_value = orig_value[:17] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 20:
                    anon_value = anon_value[:17] + "..."
                
                status = info["status"]
                if info["changed"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(uid_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Structure attributes
            for tag, info in results["structure_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if info["preserved"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(structure_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Optional anonymization tags
            for tag, info in results["optional_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                # Evaluate according to the selected anonymization level.
                if self.anonymization_level.get() == "full":
                    if info["changed"]:
                        status = "✅ " + status
                    else:
                        status = "❌ " + status
                else:
                    # Either outcome is acceptable for partial anonymization.
                    status = "✅ " + status
                
                self.tree.insert(optional_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # RT-specific attributes
            for tag, info in results["rt_specific_tags"].items():
                orig_value = info["original"]
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = info["anonymized"]
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if status in {"correctly preserved", "correctly anonymized"}:
                    status = "✅ " + status
                elif status in {"unchanged", "expected anatomy name changed", "not anonymized"}:
                    status = "❌ " + status
                else:
                    status = "ℹ️ " + status
                
                self.tree.insert(rt_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Private tags
            private_group = self.tree.insert("", "end", text="Private Tags", open=True)
            original_count = results["private_tags"]["original_count"]
            anonymized_count = results["private_tags"]["anonymized_count"]
            
            status = "✅ All removed" if anonymized_count == 0 else f"❌ {anonymized_count} remain"
            self.tree.insert(private_group, "end", text="Private tag count",
                           values=(str(original_count), str(anonymized_count), status))
            
            # Pixel data, when present
            if results["pixel_data"]["original_shape"] is not None:
                pixel_group = self.tree.insert("", "end", text="Pixel Data", open=True)
                orig_shape = results["pixel_data"]["original_shape"]
                anon_shape = results["pixel_data"]["anonymized_shape"]
                
                shape_match = orig_shape == anon_shape
                pixel_match = results["pixel_data"]["match"]
                
                shape_status = "✅ Match" if shape_match else "❌ Mismatch"
                self.tree.insert(pixel_group, "end", text="Image shape",
                               values=(str(orig_shape), str(anon_shape), shape_status))
                
                pixel_status = "✅ Match" if pixel_match else "❌ Mismatch"
                self.tree.insert(pixel_group, "end", text="Pixel values",
                               values=("Original data", "Anonymized data", pixel_status))
            
        except Exception as e:
            self.log_message(f"Details-tree update failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def generate_summary_report(self, summary):
        """Generate and save a validation summary report."""
        try:
            report = []
            
            report.append("=== Anonymization Validation Summary ===")
            report.append(f"Validation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Total files: {summary['total_files']}")
            report.append(f"Matched files: {summary['matched_files']}")
            report.append("")
            
            # Overall anonymization status
            total_must_tags = len(self.must_anonymize_tags) * summary['matched_files']
            total_anonymized = sum(summary['must_anonymize_stats'][tag]['anonymized'] for tag in self.must_anonymize_tags)
            
            if total_must_tags > 0:
                anonymization_rate = total_anonymized / total_must_tags * 100
                report.append(f"Required-tag anonymization rate: {anonymization_rate:.1f}%")
                
                if anonymization_rate >= 95:
                    report.append("✅ Overall status: Good (at least 95% of required tags were anonymized)")
                elif anonymization_rate >= 80:
                    report.append("⚠️ Overall status: Review needed (80-95% of required tags were anonymized)")
                else:
                    report.append("❌ Overall status: Insufficient (less than 80% of required tags were anonymized)")
            
            report.append("")
            report.append("--- Required Anonymization Tags ---")
            for tag in self.must_anonymize_tags:
                anonymized = summary['must_anonymize_stats'][tag]['anonymized']
                not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
                total = anonymized + not_anonymized
                
                if total > 0:
                    rate = anonymized / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {anonymized}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- UID Changes ---")
            for tag in self.uid_tags:
                changed = summary['uid_stats'][tag]['changed']
                not_changed = summary['uid_stats'][tag]['not_changed']
                total = changed + not_changed
                
                if total > 0:
                    rate = changed / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {changed}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- Structure Preservation ---")
            for tag in self.structure_tags:
                preserved = summary['structure_stats'][tag]['preserved']
                not_preserved = summary['structure_stats'][tag]['not_preserved']
                total = preserved + not_preserved
                
                if total > 0:
                    rate = preserved / total * 100
                    status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                    report.append(f"{status} {tag}: {preserved}/{total} ({rate:.1f}%)")
            
            report.append("")
            report.append("--- Private-Tag Removal ---")
            removed = summary['private_tags_stats']['removed']
            not_removed = summary['private_tags_stats']['not_removed']
            total = removed + not_removed
            
            if total > 0:
                rate = removed / total * 100
                status = "✅" if rate >= 95 else "⚠️" if rate >= 80 else "❌"
                report.append(f"{status} Private tags removed: {removed}/{total} ({rate:.1f}%)")
            
            # Modality distribution
            report.append("")
            report.append("--- Modality Distribution ---")
            for modality, count in summary['modality_stats'].items():
                report.append(f"{modality}: {count} files")
            
            # Patient-ID mapping
            if summary['patient_id_map']:
                report.append("")
                report.append("--- Patient-ID Mapping (up to 10 entries) ---")
                count = 0
                for orig_id, anon_id in summary['patient_id_map'].items():
                    # Mask part of the original patient ID.
                    if len(orig_id) > 4:
                        masked_id = orig_id[:2] + "***" + orig_id[-2:]
                    else:
                        masked_id = "***"
                        
                    report.append(f"{masked_id} → {anon_id}")
                    count += 1
                    if count >= 10:
                        report.append(f"...and {len(summary['patient_id_map']) - 10} more")
                        break
            
            # Save the report.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = Path(self.report_dir_var.get()) / f"validation_summary_{timestamp}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))
            
            self.log_message(f"Summary report saved: {report_path}")
            
            return "\n".join(report)
            
        except Exception as e:
            self.log_message(f"Report generation failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
    
    def draw_validation_graphs(self, summary):
        """Plot required-tag anonymization rates."""
        try:
            self.ax.clear()
            
            # Calculate anonymization rates.
            tags = self.must_anonymize_tags
            anonymized_rates = []
            
            for tag in tags:
                anonymized = summary['must_anonymize_stats'][tag]['anonymized']
                not_anonymized = summary['must_anonymize_stats'][tag]['not_anonymized']
                total = anonymized + not_anonymized
                
                if total > 0:
                    rate = anonymized / total * 100
                else:
                    rate = 0
                
                anonymized_rates.append(rate)
            
            # Truncate long tag names.
            short_tags = [tag[:15] + '...' if len(tag) > 15 else tag for tag in tags]
            
            # Draw bars.
            bar_colors = ['green' if rate >= 95 else 'orange' if rate >= 80 else 'red' for rate in anonymized_rates]
            bars = self.ax.bar(short_tags, anonymized_rates, color=bar_colors)
            
            # Graph settings
            self.ax.set_title('Required-Tag Anonymization Rate')
            self.ax.set_xlabel('Tag')
            self.ax.set_ylabel('Anonymization Rate (%)')
            self.ax.set_ylim(0, 100)
            
            # Rotate x-axis labels.
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            # Display values.
            for bar in bars:
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', rotation=0)
            
            # Add threshold lines.
            self.ax.axhline(y=95, color='green', linestyle='--', alpha=0.5)
            self.ax.axhline(y=80, color='orange', linestyle='--', alpha=0.5)
            
            self.ax.tick_params(axis='x', labelsize=8)
            self.figure.tight_layout()
            
            self.canvas.draw()
            
        except Exception as e:
            self.log_message(f"Graph rendering failed: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    def start_validation(self):
        """Start validation in a background thread."""
        if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
            messagebox.showerror("Error", "Select both the original and anonymized directories.")
            return
        
        original_dir = Path(self.original_dir_var.get())
        anonymized_dir = Path(self.anonymized_dir_var.get())
        
        if not original_dir.exists() or not anonymized_dir.exists():
            messagebox.showerror("Error", "One or more selected directories do not exist.")
            return
        
        # Do not start a second run while one is active.
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            messagebox.showwarning("Warning", "Validation is already running.")
            return
        
        # Clear previous output.
        self.log_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # Start processing.
        self.status_var.set("Starting validation...")
        self.log_message("Starting validation...")
        
        # Run in the background.
        self.process_thread = threading.Thread(
            target=self.run_validation_thread, 
            args=(original_dir, anonymized_dir)
        )
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def run_validation_thread(self, original_dir, anonymized_dir):
        """Run validation in the worker thread."""
        try:
            report = self.validate_files(original_dir, anonymized_dir)
            
            if report:
                # Display the summary.
                self.status_var.set("Validation complete")
                self.update_summary(report)
                
                # Show the summary tab.
                if self.root:
                    self.notebook.select(1)
                    messagebox.showinfo("Validation Complete", "Validation is complete. Review the results on the Summary tab.")
            else:
                self.status_var.set("Validation error")
                messagebox.showerror("Error", "An error occurred during validation.")
                
        except Exception as e:
            error_msg = f"Validation worker failed: {str(e)}"
            self.log_message(error_msg)
            self.logger.error(traceback.format_exc())
            self.status_var.set("An error occurred")
            messagebox.showerror("Error", error_msg)


def main():
    """Run the command-line or graphical validator."""
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(description='RT DICOM anonymization validator')
    parser.add_argument('--nogui', action='store_true', help='Run without the graphical interface')
    parser.add_argument('--original', help='Path to the original DICOM directory')
    parser.add_argument('--anonymized', help='Path to the anonymized DICOM directory')
    parser.add_argument('--report', help='Path to the report output directory')
    args = parser.parse_args()
    
    if args.nogui:
        # Command-line mode
        print("Running in command-line mode...")
        validator = RTDicomValidator()
        
        # Apply command-line directory overrides.
        if args.original:
            validator.original_dir = Path(args.original)
        if args.anonymized:
            validator.anonymized_dir = Path(args.anonymized)
        if args.report:
            validator.report_dir = Path(args.report)
            
        report = validator.validate_files(validator.original_dir, validator.anonymized_dir)
        if report:
            print("\n" + report)
    else:
        # GUI mode
        print("Running in GUI mode...")
        root = tk.Tk()
        app = RTDicomValidator(root)
        root.mainloop()

if __name__ == '__main__':
    print("Starting the validation program...")
    main()
