import tkinter as tk
import ttkbootstrap as tb
from password_manager import PasswordManager
from screen_protection import ScreenProtection


def on_closing():
    screen_protection.stop_protection()
    root.destroy()

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    screen_protection = ScreenProtection(root)
    app = PasswordManager(root)
    
    # Start the screen protection mechanisms after initializing the app
    screen_protection.start_protection()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()