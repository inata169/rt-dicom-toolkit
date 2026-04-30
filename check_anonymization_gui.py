#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DICOM Anonymization Checker GUI
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    print("エラー: customtkinter がインストールされていません。")
    print("インストール方法: pip install customtkinter")
    exit(1)

from check_anonymization import AnonymizationChecker

# CustomTkinterの全体設定
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CheckerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DICOM Anonymization Checker")
        self.geometry("800x650")
        
        # Grid configure
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- Title Frame ----------------
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.title_frame, 
            text="DICOM 匿名化チェッカー", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left")

        # ---------------- Main Tabview ----------------
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tabview.add("単独スキャン (Scan)")
        self.tabview.add("ペア比較 (Compare)")

        self._setup_scan_tab()
        self._setup_compare_tab()

        # ---------------- Log / Output Area ----------------
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.grid_rowconfigure(2, weight=2)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="出力結果", font=ctk.CTkFont(weight="bold"))
        self.log_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.log_textbox = ctk.CTkTextbox(self.log_frame, wrap="word", font=("Consolas", 12))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.checker = AnonymizationChecker()
        self._ui_queue = queue.Queue()
        self._ui_flush_scheduled = False

    def _setup_scan_tab(self):
        tab = self.tabview.tab("単独スキャン (Scan)")
        tab.grid_columnconfigure(1, weight=1)

        lbl = ctk.CTkLabel(tab, text="スキャンするディレクトリ（匿名化済み）を選択してください:")
        lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

        self.scan_dir_var = tk.StringVar()
        entry = ctk.CTkEntry(tab, textvariable=self.scan_dir_var, placeholder_text="ディレクトリパス...")
        entry.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=5, sticky="ew")

        btn_browse = ctk.CTkButton(tab, text="参照", width=80, command=self._browse_scan_dir)
        btn_browse.grid(row=1, column=2, padx=(5, 10), pady=5)

        btn_run = ctk.CTkButton(tab, text="▶ スキャン開始", command=self._run_scan, fg_color="#28a745", hover_color="#218838")
        btn_run.grid(row=2, column=0, columnspan=3, padx=10, pady=(20, 10))

    def _setup_compare_tab(self):
        tab = self.tabview.tab("ペア比較 (Compare)")
        tab.grid_columnconfigure(1, weight=1)

        # Original Dir
        lbl_orig = ctk.CTkLabel(tab, text="原本ディレクトリ:")
        lbl_orig.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.orig_dir_var = tk.StringVar()
        entry_orig = ctk.CTkEntry(tab, textvariable=self.orig_dir_var, placeholder_text="原本のディレクトリ...")
        entry_orig.grid(row=0, column=1, padx=(5, 5), pady=10, sticky="ew")

        btn_orig = ctk.CTkButton(tab, text="参照", width=80, command=lambda: self._browse_dir(self.orig_dir_var))
        btn_orig.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Anonymized Dir
        lbl_anon = ctk.CTkLabel(tab, text="匿名化済みディレクトリ:")
        lbl_anon.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="w")

        self.anon_dir_var = tk.StringVar()
        entry_anon = ctk.CTkEntry(tab, textvariable=self.anon_dir_var, placeholder_text="匿名化済みのディレクトリ...")
        entry_anon.grid(row=1, column=1, padx=(5, 5), pady=5, sticky="ew")

        btn_anon = ctk.CTkButton(tab, text="参照", width=80, command=lambda: self._browse_dir(self.anon_dir_var))
        btn_anon.grid(row=1, column=2, padx=(5, 10), pady=5)

        btn_run = ctk.CTkButton(tab, text="▶ 比較開始", command=self._run_compare, fg_color="#28a745", hover_color="#218838")
        btn_run.grid(row=2, column=0, columnspan=3, padx=10, pady=(20, 10))

    def _browse_scan_dir(self):
        self._browse_dir(self.scan_dir_var)

    def _browse_dir(self, string_var):
        dir_path = filedialog.askdirectory()
        if dir_path:
            string_var.set(dir_path)

    def log_gui(self, message):
        if threading.current_thread() is not threading.main_thread():
            self._enqueue_ui_action(self.log_gui, message)
            return
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def _enqueue_ui_action(self, callback, *args, **kwargs):
        self._ui_queue.put((callback, args, kwargs))
        self._schedule_ui_flush()

    def _schedule_ui_flush(self):
        if self._ui_flush_scheduled:
            return
        self._ui_flush_scheduled = True
        self.after(0, self._process_ui_queue)

    def _process_ui_queue(self):
        self._ui_flush_scheduled = False
        while True:
            try:
                callback, args, kwargs = self._ui_queue.get_nowait()
            except queue.Empty:
                return
            callback(*args, **kwargs)

    def _clear_log(self):
        self.log_textbox.delete("1.0", "end")

    def _run_scan(self):
        target = self.scan_dir_var.get()
        if not target or not os.path.exists(target):
            messagebox.showerror("エラー", "有効なディレクトリを選択してください。")
            return
            
        self._clear_log()
        self.log_gui(f"[*] スキャンモードを開始します...\n対象: {target}\n")
        
        # Override console print with GUI print temporarily
        original_print = self.checker.print_colored
        self.checker.print_colored = lambda text, color="": self.log_gui(text)
        
        def task():
            try:
                res = self.checker.scan_directory(target)
                self.checker.generate_report(res)
            except Exception as e:
                self.log_gui(f"\n[エラー] {str(e)}")
            finally:
                self._enqueue_ui_action(self._on_background_task_done, original_print)

        threading.Thread(target=task, daemon=True).start()

    def _run_compare(self):
        orig = self.orig_dir_var.get()
        anon = self.anon_dir_var.get()
        
        if not orig or not os.path.exists(orig) or not anon or not os.path.exists(anon):
            messagebox.showerror("エラー", "両方の有効なディレクトリを選択してください。")
            return
            
        self._clear_log()
        self.log_gui(f"[*] ペア比較モードを開始します...\n原本: {orig}\n匿名化: {anon}\n")
        
        # Override console print with GUI print temporarily
        original_print = self.checker.print_colored
        self.checker.print_colored = lambda text, color="": self.log_gui(text)
        
        def task():
            try:
                res = self.checker.compare_directories(orig, anon)
                self.checker.generate_report(res)
            except Exception as e:
                self.log_gui(f"\n[エラー] {str(e)}")
            finally:
                self._enqueue_ui_action(self._on_background_task_done, original_print)

        threading.Thread(target=task, daemon=True).start()

    def _on_background_task_done(self, original_print):
        self.checker.print_colored = original_print
        self.log_gui("\n処理が完了しました。")

if __name__ == "__main__":
    app = CheckerGUI()
    app.mainloop()
