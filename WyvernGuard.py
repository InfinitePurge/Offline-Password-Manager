import tkinter as tk
import ttkbootstrap as tb
from password_manager import PasswordManager

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = PasswordManager(root)
    root.mainloop()