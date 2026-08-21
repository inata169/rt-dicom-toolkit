"""
Shared GUI widgets.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DirectorySelector(ttk.Frame):
    """Directory-selection frame."""
    
    def __init__(self, parent, label_text, initial_dir, browse_command):
        """
        Initialize the directory-selection frame.
        
        Args:
            parent: Parent widget.
            label_text: Label text.
            initial_dir: Initial directory.
            browse_command: Browse-button callback.
        """
        super().__init__(parent)
        
        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=5)
        
        self.dir_var = tk.StringVar(value=str(initial_dir))
        ttk.Entry(self, textvariable=self.dir_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(self, text="Browse...", command=browse_command).pack(side=tk.LEFT)
    
    def get(self):
        """Return the selected directory path."""
        return Path(self.dir_var.get())
    
    def set(self, path):
        """Set the directory path."""
        self.dir_var.set(str(path))


class LogTextFrame(ttk.LabelFrame):
    """Scrollable log-text frame."""
    
    def __init__(self, parent, title="Log"):
        """
        Initialize the log-text frame.
        
        Args:
            parent: Parent widget.
            title: Frame title.
        """
        super().__init__(parent, text=title, padding="5")
        
        self.text = tk.Text(self, height=15, width=70, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(self.text, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)
    
    def append(self, message):
        """Append a message."""
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
    
    def clear(self):
        """Clear all text."""
        self.text.delete(1.0, tk.END)


class GraphFrame(ttk.LabelFrame):
    """Matplotlib graph frame."""
    
    def __init__(self, parent, title="Graph", figsize=(8, 6)):
        """
        Initialize the graph frame.
        
        Args:
            parent: Parent widget.
            title: Frame title.
            figsize: Figure size.
        """
        super().__init__(parent, text=title, padding="5")
        
        self.figure, self.ax = plt.subplots(figsize=figsize)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def draw(self):
        """Draw the current figure."""
        self.canvas.draw()
    
    def clear(self):
        """Clear the graph."""
        self.ax.clear()
        self.draw()
