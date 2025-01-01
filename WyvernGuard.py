import tkinter as tk
import ttkbootstrap as tb
from password_manager import PasswordManager
from screen_protection import ScreenProtection


def on_closing():
    app.on_closing()
    screen_protection.stop_protection()
    

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    screen_protection = ScreenProtection(root)
    # Pass screen_protection to PasswordManager
    app = PasswordManager(root, screen_protection)
    
    # Start the screen protection mechanisms after initializing the app
    screen_protection.start_protection()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()