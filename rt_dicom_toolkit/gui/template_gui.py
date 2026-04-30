import os
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from rt_dicom_toolkit.template.engine import DICOMTemplateEngine
from rt_dicom_toolkit.utils.file_utils import find_dicom_files

class TemplateApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RT DICOM Template Engine")
        self.geometry("800x600")
        self.minsize(700, 500)
        
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        self._build_ui()
        
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- 設定パネル ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        # テンプレートファイル
        self.template_label = ctk.CTkLabel(self.settings_frame, text="テンプレートDICOM:")
        self.template_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.template_entry = ctk.CTkEntry(self.settings_frame)
        self.template_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.template_btn = ctk.CTkButton(self.settings_frame, text="参照", width=80, command=self._browse_template)
        self.template_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # 入力ディレクトリ
        self.input_label = ctk.CTkLabel(self.settings_frame, text="情報抽出元 (Dir/File):")
        self.input_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.input_entry = ctk.CTkEntry(self.settings_frame)
        self.input_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        self.input_btn = ctk.CTkButton(self.settings_frame, text="参照", width=80, command=self._browse_input)
        self.input_btn.grid(row=1, column=2, padx=10, pady=10)
        
        # 出力ディレクトリ
        self.output_label = ctk.CTkLabel(self.settings_frame, text="出力ディレクトリ:")
        self.output_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.output_entry = ctk.CTkEntry(self.settings_frame)
        self.output_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        self.output_btn = ctk.CTkButton(self.settings_frame, text="参照", width=80, command=self._browse_output)
        self.output_btn.grid(row=2, column=2, padx=10, pady=10)
        
        # オプション設定
        self.options_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.options_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        self.sync_patient_var = ctk.BooleanVar(value=True)
        self.sync_patient_cb = ctk.CTkCheckBox(self.options_frame, text="患者情報を同期", variable=self.sync_patient_var)
        self.sync_patient_cb.grid(row=0, column=0, padx=20, pady=5)
        
        self.sync_geometry_var = ctk.BooleanVar(value=True)
        self.sync_geometry_cb = ctk.CTkCheckBox(self.options_frame, text="幾何学情報を同期", variable=self.sync_geometry_var)
        self.sync_geometry_cb.grid(row=0, column=1, padx=20, pady=5)
        
        # --- ログ表示パネル ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_textbox = ctk.CTkTextbox(self.log_frame)
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.configure(state="disabled")
        
        # --- ステータス・実行パネル ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="待機中...")
        self.status_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=(5, 10))
        self.progress_bar.set(0)
        
        self.run_btn = ctk.CTkButton(self.status_frame, text="合成を開始", height=40, font=("", 16, "bold"), command=self._start_processing)
        self.run_btn.grid(row=1, column=1, padx=(10, 5), pady=(5, 10))

    def _browse_template(self):
        path = filedialog.askopenfilename(title="テンプレートDICOMの選択", filetypes=[("DICOM Files", "*.dcm"), ("All Files", "*.*")])
        if path:
            self.template_entry.delete(0, 'end')
            self.template_entry.insert(0, path)

    def _browse_input(self):
        path = filedialog.askdirectory(title="情報抽出元ディレクトリの選択")
        if path:
            self.input_entry.delete(0, 'end')
            self.input_entry.insert(0, path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="出力ディレクトリの選択")
        if path:
            self.output_entry.delete(0, 'end')
            self.output_entry.insert(0, path)
            
    def _append_log(self, message):
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
            self.status_label.configure(text=f"処理中... {current}/{total} ({progress*100:.1f}%) : {filename}")
        self.after(0, update)
        
    def _processing_finished(self, success, message=""):
        def update():
            self.run_btn.configure(state="normal", text="合成を開始")
            self.status_label.configure(text="完了" if success else f"エラー: {message}")
            if success:
                messagebox.showinfo("完了", "テンプレート合成が完了しました。")
            else:
                messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{message}")
        self.after(0, update)

    def _start_processing(self):
        tmpl_path = self.template_entry.get()
        in_path = self.input_entry.get()
        out_path = self.output_entry.get()
        
        if not os.path.exists(tmpl_path) or not os.path.isfile(tmpl_path):
            messagebox.showerror("エラー", "有効なテンプレートファイルを選択してください。")
            return
            
        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("エラー", "有効な入力ディレクトリ/ファイルを選択してください。")
            return
            
        if not out_path:
            messagebox.showerror("エラー", "出力ディレクトリを選択してください。")
            return
            
        self.run_btn.configure(state="disabled", text="処理中...")
        self.progress_bar.set(0)
        self.status_label.configure(text="処理を準備中...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        threading.Thread(target=self._run_process_thread, args=(tmpl_path, in_path, out_path), daemon=True).start()
        
    def _run_process_thread(self, tmpl_path, in_path, out_path):
        try:
            self._append_log(f"テンプレート読み込み中: {tmpl_path}")
            engine = DICOMTemplateEngine(tmpl_path)
            
            input_path = Path(in_path)
            output_dir = Path(out_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            sync_patient = self.sync_patient_var.get()
            sync_geometry = self.sync_geometry_var.get()
            
            if input_path.is_file():
                files = [input_path]
            else:
                files = find_dicom_files(input_path)
                
            total = len(files)
            if total == 0:
                self._append_log("処理対象のファイルが見つかりません。")
                self._processing_finished(True)
                return
                
            for i, file_path in enumerate(files):
                self._update_progress(i + 1, total, file_path.name)
                self._append_log(f"処理中: {file_path.name}")
                
                try:
                    synced_dcm = engine.sync_from_source(
                        str(file_path), 
                        sync_patient=sync_patient, 
                        sync_geometry=sync_geometry
                    )
                    output_path = output_dir / f"tmpl_{file_path.name}"
                    synced_dcm.save_as(str(output_path), write_like_original=False)
                    self._append_log(f"  成功: -> {output_path.name}")
                except Exception as e:
                    self._append_log(f"  エラー: {e}")
                    
            self._append_log("すべての処理が完了しました。")
            self._processing_finished(True)
        except Exception as e:
            self._append_log(f"致命的なエラー: {str(e)}")
            self._processing_finished(False, str(e))

def run_template_app():
    app = TemplateApp()
    app.mainloop()

if __name__ == "__main__":
    run_template_app()
