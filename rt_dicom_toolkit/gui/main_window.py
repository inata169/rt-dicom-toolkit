import os
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from rt_dicom_toolkit.anonymizer.core import RTDicomAnonymizer

class AnonymizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings.
        self.title("RT DICOM Anonymizer")
        self.geometry("800x600")
        self.minsize(700, 500)
        
        # Theme settings.
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Core anonymizer.
        self.anonymizer = RTDicomAnonymizer()
        
        # Build the interface.
        self._build_ui()
        
    def _build_ui(self):
        # Main layout.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Settings panel.
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        # Input directory.
        self.input_label = ctk.CTkLabel(self.settings_frame, text="Input directory:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.input_entry = ctk.CTkEntry(self.settings_frame)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.input_entry.insert(0, str(self.anonymizer.input_dir))
        
        self.input_btn = ctk.CTkButton(self.settings_frame, text="Browse", width=80, command=self._browse_input)
        self.input_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Output directory.
        self.output_label = ctk.CTkLabel(self.settings_frame, text="Output directory:")
        self.output_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.output_entry = ctk.CTkEntry(self.settings_frame)
        self.output_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.output_entry.insert(0, str(self.anonymizer.output_dir))
        
        self.output_btn = ctk.CTkButton(self.settings_frame, text="Browse", width=80, command=self._browse_output)
        self.output_btn.grid(row=1, column=2, padx=10, pady=10)
        
        # Options.
        self.options_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.options_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # UID handling.
        self.uid_label = ctk.CTkLabel(self.options_frame, text="UID handling:")
        self.uid_label.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        self.uid_var = ctk.StringVar(value=self.anonymizer.uid_handling)
        self.uid_menu = ctk.CTkOptionMenu(self.options_frame, variable=self.uid_var, values=["consistent", "random", "keep"])
        self.uid_menu.grid(row=0, column=1, padx=10, pady=5)
        
        # Directory-structure preservation.
        self.keep_struct_var = ctk.BooleanVar(value=self.anonymizer.keep_structure)
        self.keep_struct_cb = ctk.CTkCheckBox(self.options_frame, text="Preserve input directory structure", variable=self.keep_struct_var)
        self.keep_struct_cb.grid(row=0, column=2, padx=20, pady=5)
        
        # Private-tag handling.
        self.private_tag_var = ctk.StringVar(value=self.anonymizer.private_tags)
        self.private_tag_cb = ctk.CTkCheckBox(self.options_frame, text="Remove private tags",
                                             variable=self.private_tag_var, onvalue="remove", offvalue="keep")
        self.private_tag_cb.grid(row=0, column=3, padx=20, pady=5)
        
        # Log panel.
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_textbox = ctk.CTkTextbox(self.log_frame)
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.configure(state="disabled")
        
        # Display core log messages in this panel.
        self.anonymizer.log_callback = self._append_log
        
        # Status and run panel.
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 10))
        self.progress_bar.set(0)
        
        self.run_btn = ctk.CTkButton(self.status_frame, text="Start anonymization", height=40, font=("", 16, "bold"), command=self._start_processing)
        self.run_btn.grid(row=1, column=1, padx=(10, 5), pady=(5, 10))

    def _browse_input(self):
        path = filedialog.askdirectory(title="Select input directory")
        if path:
            self.input_entry.delete(0, 'end')
            self.input_entry.insert(0, path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, path)
            
    def _append_log(self, message):
        # Update the text box on the GUI thread.
        def update_text():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, update_text)
        
    def _update_progress(self, current, total, filename):
        def update():
            progress = current / total if total > 0 else 0
            self.progress_bar.set(progress)
            self.status_label.configure(text=f"Processing... {current}/{total} ({progress*100:.1f}%) : {filename}")
        self.after(0, update)
        
    def _processing_finished(self, success, message=""):
        def update():
            self.run_btn.configure(state="normal", text="Start anonymization")
            self.input_btn.configure(state="normal")
            self.output_btn.configure(state="normal")
            self.status_label.configure(text="Complete" if success else f"Error: {message}")
            if success:
                messagebox.showinfo("Complete", "Anonymization completed.")
            else:
                messagebox.showerror("Error", f"An error occurred during processing:\n{message}")
        self.after(0, update)

    def _start_processing(self):
        # Validate input.
        in_path = self.input_entry.get()
        out_path = self.output_entry.get()
        
        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("Error", "Select a valid input directory.")
            return
            
        # Lock the UI while processing.
        self.run_btn.configure(state="disabled", text="Processing...")
        self.input_btn.configure(state="disabled")
        self.output_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Preparing...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        # Update anonymizer settings.
        self.anonymizer.input_dir = Path(in_path)
        self.anonymizer.output_dir = Path(out_path)
        # Store logs under the output directory.
        log_dir = Path(out_path) / "logs"
        self.anonymizer.log_dir = log_dir
        
        self.anonymizer.uid_handling = self.uid_var.get()
        self.anonymizer.keep_structure = self.keep_struct_var.get()
        self.anonymizer.private_tags = self.private_tag_var.get()
        
        # Run processing on a worker thread.
        threading.Thread(target=self._run_anonymizer_thread, daemon=True).start()
        
    def _run_anonymizer_thread(self):
        try:
            self.anonymizer.process_directory(progress_callback=self._update_progress)
            self._processing_finished(True)
        except Exception as e:
            self._processing_finished(False, str(e))

def run_app():
    app = AnonymizerApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()
