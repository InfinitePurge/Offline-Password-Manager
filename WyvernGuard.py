import tkinter as tk
import ttkbootstrap as tb
from password_manager import PasswordManager
from screen_protection import ScreenProtection


if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    screen_protection = ScreenProtection(root)
    app = PasswordManager(root)
    root.mainloop()

    def on_closing():
        screen_protection.stop_protection()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()