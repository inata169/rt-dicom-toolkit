"""
GUI for the DICOM anonymizer.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os

# Import shared matplotlib configuration.
from rt_dicom_toolkit.utils.matplotlib_utils import configure_matplotlib_for_japanese

# Prefer installed-package imports.
from rt_dicom_toolkit.anonymizer import RTDicomAnonymizer

# Fall back to a repository-relative import path.
if not "rt_dicom_toolkit" in sys.modules:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from anonymizer import RTDicomAnonymizer

class AnonymizerGUI:
    """Desktop interface for DICOM anonymization."""
    
    def __init__(self, root):
        """
        Initialize the anonymizer GUI.
        
        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title("RT DICOM Anonymizer")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # Create the anonymizer.
        self.anonymizer = RTDicomAnonymizer(self.root)
        
        # Configure the interface.
        self.setup_gui()
        
    def setup_gui(self):
        """Create GUI components."""
        # Apply shared matplotlib font settings.
        configure_matplotlib_for_japanese()
        
        # Main frame.
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Directory settings.
        dir_frame = ttk.LabelFrame(main_frame, text="Directories", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        # Input directory.
        ttk.Label(dir_frame, text="Input directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=str(self.anonymizer.input_dir))
        ttk.Entry(dir_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_input_dir).grid(row=0, column=2, pady=5)

        # Output directory.
        ttk.Label(dir_frame, text="Output directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=str(self.anonymizer.output_dir))
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_output_dir).grid(row=1, column=2, pady=5)

        # Log directory.
        ttk.Label(dir_frame, text="Log directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_dir_var = tk.StringVar(value=str(self.anonymizer.log_dir))
        ttk.Entry(dir_frame, textvariable=self.log_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_log_dir).grid(row=2, column=2, pady=5)
        
        # Anonymization settings.
        settings_frame = ttk.LabelFrame(main_frame, text="Anonymization settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Anonymization level.
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
        self.anonymizer.progress_var = self.progress_var
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, 
                                           mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Log text area.
        self.log_text = tk.Text(progress_frame, height=15, width=70, wrap=tk.WORD)
        self.anonymizer.log_text = self.log_text
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar.
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar.
        self.status_var = tk.StringVar(value="Ready")
        self.anonymizer.status_var = self.status_var
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_input_dir(self):
        """Select an input directory."""
        directory = filedialog.askdirectory(title="Select a directory containing DICOM files")
        if directory:
            self.input_dir_var.set(directory)
            self.anonymizer.input_dir = Path(directory)
            self.anonymizer.log_message(f"Input directory set: {directory}")
    
    def browse_output_dir(self):
        """Select an output directory."""
        directory = filedialog.askdirectory(title="Select the anonymized-output directory")
        if directory:
            self.output_dir_var.set(directory)
            self.anonymizer.output_dir = Path(directory)
            self.anonymizer.log_message(f"Output directory set: {directory}")
    
    def browse_log_dir(self):
        """Select a log directory."""
        directory = filedialog.askdirectory(title="Select the log directory")
        if directory:
            self.log_dir_var.set(directory)
            self.anonymizer.log_dir = Path(directory)
            self.anonymizer.log_message(f"Log directory set: {directory}")
    
    def check_directory(self):
        """Inspect the selected directory."""
        if not self.input_dir_var.get():
            messagebox.showerror("Error", "Select an input directory.")
            return
            
        input_dir = Path(self.input_dir_var.get())
        if not input_dir.exists():
            messagebox.showerror("Error", "The input directory does not exist.")
            return
            
        self.anonymizer.log_message(f"Inspecting directory '{input_dir}'...")
        
        # Inspect on a worker thread.
        self.process_thread = threading.Thread(target=self._check_directory_thread, args=(input_dir,))
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _check_directory_thread(self, input_dir):
        """Run directory inspection on a worker thread."""
        from rt_dicom_toolkit.utils.file_utils import find_dicom_files
        from rt_dicom_toolkit.utils.dicom_utils import get_dicom_info
        
        try:
            # Find DICOM files.
            files = find_dicom_files(input_dir)
            self.anonymizer.log_message(f"Found {len(files)} total files")
            
            # Read DICOM information.
            dicom_count = 0
            for file_path in files[:20]:  # Display details for at most 20 files.
                try:
                    info = get_dicom_info(file_path)
                    if info:
                        dicom_count += 1
                        modality = info.get('Modality', 'Unknown')
                        patient_id = info.get('PatientID', 'Unknown')
                        
                        # Mask the patient ID.
                        if patient_id != 'Unknown':
                            id_str = str(patient_id)
                            if len(id_str) > 4:
                                patient_id = id_str[:2] + "***" + id_str[-2:]
                            else:
                                patient_id = "***"
                        
                        self.anonymizer.log_message(f"DICOM: {file_path.name}, Modality: {modality}, Patient ID: {patient_id}")
                except Exception as e:
                    self.anonymizer.log_message(f"File-read error {file_path.name}: {str(e)}")
            
            if len(files) > 20:
                self.anonymizer.log_message(f"...and {len(files) - 20} more files")
            
            self.anonymizer.log_message(f"Inspection complete: {len(files)} total files, {dicom_count} DICOM files")
            
            if dicom_count == 0:
                self.anonymizer.log_message("Warning: no DICOM files were found.")
                messagebox.showwarning("Warning", "No DICOM files were found in the input directory.")
        
        except Exception as e:
            self.anonymizer.log_message(f"Directory-inspection error: {str(e)}")
    
    def start_processing(self):
        """Start anonymization."""
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
        
        # Apply current settings.
        self.anonymizer.input_dir = Path(self.input_dir_var.get())
        self.anonymizer.output_dir = Path(self.output_dir_var.get())
        self.anonymizer.log_dir = Path(self.log_dir_var.get())
        self.anonymizer.anonymization_level = self.anonymization_level.get()
        self.anonymizer.private_tags = self.private_tags.get()
        self.anonymizer.uid_handling = self.uid_handling.get()
        self.anonymizer.keep_structure = self.keep_structure.get()
        self.anonymizer.patient_id_method = self.patient_id_method.get()
        
        # Clear previous logs.
        self.log_text.delete(1.0, tk.END)
        
        # Start processing.
        self.status_var.set("Starting processing...")
        self.progress_var.set(0)
        self.anonymizer.log_message("Starting worker thread...")
        
        # Run processing in the background.
        self.process_thread = threading.Thread(target=self.anonymizer.process_directory)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # Report whether the worker started.
        self.anonymizer.log_message(
            f"Worker status: {'running' if self.process_thread.is_alive() else 'failed to start'}"
        )


def run_anonymizer_gui():
    """Run the anonymizer GUI."""
    root = tk.Tk()
    app = AnonymizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_anonymizer_gui()
