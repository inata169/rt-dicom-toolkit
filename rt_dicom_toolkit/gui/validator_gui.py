"""
GUI for DICOM anonymization validation.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os

# Import shared matplotlib configuration.
from rt_dicom_toolkit.utils.matplotlib_utils import configure_matplotlib_for_japanese

# Prefer installed-package imports.
from rt_dicom_toolkit.validator import RTDicomValidator
from rt_dicom_toolkit.validator.rules import ValidationRules

# Fall back to a repository-relative import path.
if not "rt_dicom_toolkit" in sys.modules:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from validator import RTDicomValidator
    from validator.rules import ValidationRules

class ValidatorGUI:
    """Desktop interface for DICOM anonymization validation."""
    
    def __init__(self, root):
        """
        Initialize the validator GUI.
        
        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title("RT DICOM Anonymization Validator")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Create the validator.
        self.validator = RTDicomValidator(self.root)
        
        # Configure the interface.
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        """Close the Tk event loop and destroy the window."""
        self.root.quit()
        self.root.destroy()
        
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
        
        # Original directory.
        ttk.Label(dir_frame, text="Original directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.original_dir_var = tk.StringVar(value=str(self.validator.original_dir))
        ttk.Entry(dir_frame, textvariable=self.original_dir_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_original_dir).grid(row=0, column=2, pady=5)
        
        # Anonymized directory.
        ttk.Label(dir_frame, text="Anonymized directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.anonymized_dir_var = tk.StringVar(value=str(self.validator.anonymized_dir))
        ttk.Entry(dir_frame, textvariable=self.anonymized_dir_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_anonymized_dir).grid(row=1, column=2, pady=5)
        
        # Report directory.
        ttk.Label(dir_frame, text="Report directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.report_dir_var = tk.StringVar(value=str(self.validator.report_dir))
        ttk.Entry(dir_frame, textvariable=self.report_dir_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_report_dir).grid(row=2, column=2, pady=5)
        
        # Validation settings.
        settings_frame = ttk.LabelFrame(main_frame, text="Validation settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Anonymization level.
        ttk.Label(settings_frame, text="Anonymization level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.anonymization_level = tk.StringVar(value="full")
        self.validator.anonymization_level = self.anonymization_level
        ttk.Radiobutton(settings_frame, text="Full", variable=self.anonymization_level,
                       value="full").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(settings_frame, text="Partial (retain dates and institution)", variable=self.anonymization_level,
                       value="partial").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Private-tag check.
        ttk.Label(settings_frame, text="Private tags:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.check_private_tags = tk.BooleanVar(value=True)
        self.validator.check_private_tags = self.check_private_tags
        ttk.Checkbutton(settings_frame, text="Verify private-tag removal",
                        variable=self.check_private_tags).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Structure preservation.
        ttk.Label(settings_frame, text="Structure:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.check_file_structure = tk.BooleanVar(value=True)
        self.validator.check_file_structure = self.check_file_structure
        ttk.Checkbutton(settings_frame, text="Verify file-structure preservation",
                       variable=self.check_file_structure).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # UID check.
        ttk.Label(settings_frame, text="UIDs:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.check_uid_changed = tk.BooleanVar(value=True)
        self.validator.check_uid_changed = self.check_uid_changed
        ttk.Checkbutton(settings_frame, text="Verify that all configured UIDs changed",
                        variable=self.check_uid_changed).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Detailed report.
        ttk.Label(settings_frame, text="Report detail:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.detailed_report = tk.BooleanVar(value=True)
        self.validator.detailed_report = self.detailed_report
        ttk.Checkbutton(settings_frame, text="Generate a detailed report",
                        variable=self.detailed_report).grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Action buttons.
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Run validation", command=self.start_validation).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Compare directories", command=self.compare_directories).pack(side=tk.RIGHT, padx=5)
        
        # Tabbed interface.
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log tab.
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        
        # Log text area.
        self.log_text = tk.Text(log_frame, height=15, width=70, wrap=tk.WORD)
        self.validator.log_text = self.log_text
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar.
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Summary tab.
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        
        # Summary text area.
        self.summary_text = tk.Text(summary_frame, height=15, width=70, wrap=tk.WORD)
        self.validator.summary_text = self.summary_text
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar.
        summary_scrollbar = ttk.Scrollbar(self.summary_text, command=self.summary_text.yview)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_text.config(yscrollcommand=summary_scrollbar.set)
        
        # Graph tab.
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Graphs")
        
        # Graph canvas.
        # Construct an unmanaged Figure so Matplotlib does not create a hidden
        # Tk root that would keep Python alive after this window is closed.
        self.figure = Figure(figsize=(8, 6))
        self.ax = self.figure.add_subplot(111)
        self.validator.figure = self.figure
        self.validator.ax = self.ax
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.validator.canvas = self.canvas
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Details tab.
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Details")
        
        # Result tree.
        self.tree = ttk.Treeview(details_frame)
        self.validator.tree = self.tree
        self.tree["columns"] = ("Original", "Anonymized", "Status")
        self.tree.column("#0", width=200, minwidth=200)
        self.tree.column("Original", width=200, minwidth=200)
        self.tree.column("Anonymized", width=200, minwidth=200)
        self.tree.column("Status", width=100, minwidth=100)
        
        self.tree.heading("#0", text="Attribute")
        self.tree.heading("Original", text="Original")
        self.tree.heading("Anonymized", text="Anonymized")
        self.tree.heading("Status", text="Status")
        
        # Tree scrollbar.
        tree_scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Layout.
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar.
        self.status_var = tk.StringVar(value="Ready")
        self.validator.status_var = self.status_var
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Expose GUI update callbacks to the validator.
        self.validator.update_treeview = self.update_treeview
        
        # Expose graph rendering to the validator.
        self.validator.draw_validation_graphs = self.draw_validation_graphs
    
    def browse_original_dir(self):
        """Select the original DICOM directory."""
        directory = filedialog.askdirectory(title="Select the original DICOM directory")
        if directory:
            self.original_dir_var.set(directory)
            self.validator.original_dir = Path(directory)
            self.validator.log_message(f"Original directory set: {directory}")
    
    def browse_anonymized_dir(self):
        """Select the anonymized DICOM directory."""
        directory = filedialog.askdirectory(title="Select the anonymized DICOM directory")
        if directory:
            self.anonymized_dir_var.set(directory)
            self.validator.anonymized_dir = Path(directory)
            self.validator.log_message(f"Anonymized directory set: {directory}")
    
    def browse_report_dir(self):
        """Select the validation-report directory."""
        directory = filedialog.askdirectory(title="Select the validation-report directory")
        if directory:
            self.report_dir_var.set(directory)
            self.validator.report_dir = Path(directory)
            self.validator.log_message(f"Report directory set: {directory}")
    
    def update_treeview(self, results, clear=True):
        """Update the result tree."""
        try:
            # Clear the tree only for the first result.
            if clear:
                self.tree.delete(*self.tree.get_children())
                
                # Create groups for each validation category.
                self.must_anonymize_group = self.tree.insert("", "end", text="Required anonymization", open=True)
                self.uid_group = self.tree.insert("", "end", text="UIDs", open=True)
                self.structure_group = self.tree.insert("", "end", text="Structure", open=True)
                self.optional_group = self.tree.insert("", "end", text="Optional anonymization", open=True)
                self.rt_group = self.tree.insert("", "end", text="RT-specific attributes", open=True)
                self.private_group = self.tree.insert("", "end", text="Private tags", open=True)
                self.pixel_group = self.tree.insert("", "end", text="Pixel Data", open=True)
            
            # Add required anonymization attributes.
            for tag, info in results["must_anonymize"].items():
                # Shorten long original values.
                orig_value = str(info["original"])
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                # Shorten long anonymized values.
                anon_value = str(info["anonymized"])
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                # Select the status icon.
                status = info["status"]
                if info["anonymized"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.must_anonymize_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Add UID results.
            for tag, info in results["uid_tags"].items():
                # Shorten UIDs for display.
                orig_value = str(info["original"])
                if len(orig_value) > 20:
                    orig_value = orig_value[:17] + "..."
                
                anon_value = str(info["anonymized"])
                if len(anon_value) > 20:
                    anon_value = anon_value[:17] + "..."
                
                status = info["status"]
                if info["changed"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.uid_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Add structure results.
            for tag, info in results["structure_tags"].items():
                orig_value = str(info["original"])
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = str(info["anonymized"])
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if info["preserved"]:
                    status = "✅ " + status
                else:
                    status = "❌ " + status
                
                self.tree.insert(self.structure_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Add optional anonymization results.
            for tag, info in results["optional_tags"].items():
                orig_value = str(info["original"])
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = str(info["anonymized"])
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                # Interpret results according to the selected level.
                if self.anonymization_level.get() == "full":
                    if info["changed"]:
                        status = "✅ " + status
                    else:
                        status = "❌ " + status
                else:
                    # A preserved value is acceptable in partial mode.
                    status = "✅ " + status
                
                self.tree.insert(self.optional_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Add RT-specific results.
            for tag, info in results["rt_specific_tags"].items():
                orig_value = str(info["original"])
                if len(orig_value) > 50:
                    orig_value = orig_value[:47] + "..."
                
                anon_value = str(info["anonymized"])
                if len(anon_value) > 50:
                    anon_value = anon_value[:47] + "..."
                
                status = info["status"]
                if "correctly" in status:
                    status = "✅ " + status
                elif "unchanged" in status or "expected" in status or "not anonymized" in status:
                    status = "❌ " + status
                else:
                    status = "ℹ️ " + status
                
                self.tree.insert(self.rt_group, "end", text=tag, values=(orig_value, anon_value, status))
            
            # Add private-tag results.
            original_count = results["private_tags"]["original_count"]
            anonymized_count = results["private_tags"]["anonymized_count"]
            
            status = "✅ All removed" if anonymized_count == 0 else f"❌ {anonymized_count} remain"
            self.tree.insert(self.private_group, "end", text="Private-tag count",
                           values=(f"{original_count}", f"{anonymized_count}", status))
            
            # Add Pixel Data results when available.
            if results["pixel_data"]["original_shape"] is not None:
                orig_shape = results["pixel_data"]["original_shape"]
                anon_shape = results["pixel_data"]["anonymized_shape"]
                
                shape_match = orig_shape == anon_shape
                pixel_match = results["pixel_data"]["match"]
                
                shape_status = "✅ Match" if shape_match else "❌ Mismatch"
                self.tree.insert(self.pixel_group, "end", text="Image shape",
                               values=(str(orig_shape), str(anon_shape), shape_status))
                
                pixel_status = "✅ Match" if pixel_match else "❌ Mismatch"
                self.tree.insert(self.pixel_group, "end", text="Pixel values",
                               values=("Original data", "Anonymized data", pixel_status))
            
        except Exception as e:
            self.validator.log_message(f"Result-tree update error: {str(e)}")
    
    def draw_validation_graphs(self, summary):
        """Render validation results as a graph."""
        try:
            self.ax.clear()
            
            # Calculate anonymization rates.
            tags = self.validator.rules.must_anonymize_tags
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
            
            # Shorten long attribute names.
            short_tags = [tag[:15] + '...' if len(tag) > 15 else tag for tag in tags]
            
            # Draw the bar chart.
            bar_colors = ['green' if rate >= 95 else 'orange' if rate >= 80 else 'red' for rate in anonymized_rates]
            bars = self.ax.bar(short_tags, anonymized_rates, color=bar_colors)
            
            # Configure the graph.
            self.ax.set_title('Required-attribute anonymization rate')
            self.ax.set_xlabel('Attribute')
            self.ax.set_ylabel('Anonymization rate (%)')
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
            self.validator.log_message(f"Graph-rendering error: {str(e)}")
    
    def compare_directories(self):
        """Start a basic directory comparison."""
        if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
            messagebox.showerror("Error", "Select both original and anonymized directories.")
            return
            
        # Apply current directory paths.
        self.validator.original_dir = Path(self.original_dir_var.get())
        self.validator.anonymized_dir = Path(self.anonymized_dir_var.get())
        
        # Compare on a worker thread.
        self.process_thread = threading.Thread(target=self._compare_directories_thread)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _compare_directories_thread(self):
        """Run directory comparison on a worker thread."""
        from rt_dicom_toolkit.utils.file_utils import compare_directory_structure
        
        try:
            # Compare directories.
            result = compare_directory_structure(
                self.validator.original_dir, 
                self.validator.anonymized_dir,
                self.validator.log_message
            )
            
            # Display results.
            self.validator.summary_text.delete(1.0, tk.END)
            for line in result["summary"]:
                self.validator.update_summary(line)
            
            # Draw the comparison graph.
            if "modality_data" in result:
                self.validator.ax.clear()
                
                modalities = result["modality_data"]["modalities"]
                original_counts = result["modality_data"]["original_counts"]
                anonymized_counts = result["modality_data"]["anonymized_counts"]
                
                # Plot Modality counts.
                x = range(len(modalities))
                width = 0.35
                
                self.validator.ax.bar([i - width/2 for i in x], original_counts, width, label='Original')
                self.validator.ax.bar([i + width/2 for i in x], anonymized_counts, width, label='Anonymized')
                
                self.validator.ax.set_title('Modality distribution comparison')
                self.validator.ax.set_xlabel('Modality')
                self.validator.ax.set_ylabel('File count')
                self.validator.ax.set_xticks(x)
                self.validator.ax.set_xticklabels(modalities)
                self.validator.ax.legend()
                
                self.validator.canvas.draw()
            
            # Switch to the details tab.
            self.notebook.select(3)
            
        except Exception as e:
            error_msg = f"Directory-comparison error: {str(e)}"
            self.validator.log_message(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def start_validation(self):
        """Start validation."""
        if not self.original_dir_var.get() or not self.anonymized_dir_var.get():
            messagebox.showerror("Error", "Select both original and anonymized directories.")
            return
                
        original_dir = Path(self.original_dir_var.get())
        anonymized_dir = Path(self.anonymized_dir_var.get())
        
        if not original_dir.exists() or not anonymized_dir.exists():
            messagebox.showerror("Error", "One or both specified directories do not exist.")
            return
        
        # Do not start while another run is active.
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            messagebox.showwarning("Warning", "Processing is already running.")
            return
        
        # Apply current settings.
        self.validator.original_dir = original_dir
        self.validator.anonymized_dir = anonymized_dir
        self.validator.report_dir = Path(self.report_dir_var.get())
        
        # Clear previous logs.
        self.log_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # Start processing.
        self.status_var.set("Starting validation...")
        self.validator.log_message("Starting validation...")
        
        # Run validation in the background.
        self.process_thread = threading.Thread(
            target=self.run_validation_thread, 
            args=(original_dir, anonymized_dir)
        )
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def run_validation_thread(self, original_dir, anonymized_dir):
        """Run validation on a worker thread."""
        try:
            report = self.validator.validate_files(original_dir, anonymized_dir)
            
            if report:
                # Display the summary.
                self.status_var.set("Validation complete")
                self.validator.update_summary(report)
                
                # Switch to the details tab.
                self.notebook.select(3)
                messagebox.showinfo("Validation complete", "Validation completed. Review per-attribute results on the Details tab and aggregate statistics on the Summary tab.")
            else:
                self.status_var.set("Validation error")
                messagebox.showerror("Error", "An error occurred during validation.")
                
        except Exception as e:
            error_msg = f"Validation worker error: {str(e)}"
            self.validator.log_message(error_msg)
            self.status_var.set("An error occurred")
            messagebox.showerror("Error", error_msg)


def run_validator_gui():
    """Run the validator GUI."""
    root = tk.Tk()
    app = ValidatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_validator_gui()
