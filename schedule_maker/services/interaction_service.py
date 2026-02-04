"""
상호작용 서비스
사용자에게 메시지를 표시하거나 입력을 받는 기능을 캡슐화
"""
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog

class InteractionService:
    """
    GUI 프레임워크에 종속적인 상호작용 로직을 처리하는 서비스
    """
    
    def __init__(self, root_window=None):
        self.root_window = root_window
        
    def set_root_window(self, window):
        self.root_window = window
        
    def show_info(self, title: str, message: str):
        messagebox.showinfo(title, message, parent=self.root_window)
        
    def show_warning(self, title: str, message: str):
        messagebox.showwarning(title, message, parent=self.root_window)
        
    def show_error(self, title: str, message: str):
        messagebox.showerror(title, message, parent=self.root_window)
        
    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=self.root_window)
        
    def ask_filename_save(self, **kwargs) -> str:
        return filedialog.asksaveasfilename(parent=self.root_window, **kwargs)
        
    def ask_filename_open(self, **kwargs) -> str:
        return filedialog.askopenfilename(parent=self.root_window, **kwargs)
        
    def ask_string(self, title: str, prompt: str) -> str:
        return simpledialog.askstring(title, prompt, parent=self.root_window)
