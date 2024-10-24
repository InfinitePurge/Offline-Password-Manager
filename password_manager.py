import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import Menu
from cryptography.fernet import InvalidToken
import csv
import os
import uuid
from tkinter import filedialog
import hashlib
import base64
from two_factor_auth import TwoFactorAuth
from PIL import Image, ImageTk
from io import BytesIO
import json
from tkinter import scrolledtext
import cryptography
from datetime import datetime, timedelta
import webbrowser
from stegano import lsb
from PIL import Image
import io
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from encryption import *
import utils
from utils import *
from translations import translations
from auto_logout import AutoLogout
from tkinter import simpledialog
from typing import Optional
import threading
import pyperclip
import gc
import markdown
import winreg
from face_recognition_auth import FaceRecognitionAuth
import cv2
import face_recognition
import sys



def get_resource_path(relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title("WyvernGuard")
        self.root.geometry("1200x700")
        self.center_window(1200, 700)
        self.theme = self.load_theme_preference()
        self.style = tb.Style(theme=self.theme)
        self.category_var = tk.StringVar()
        self.configure_button_styles()
        self.navigation_history = []
        self.categories = self.clean_categories()
        self.sidebar_buttons = []
        self.button_vars = {}
        self.expired_passwords = set()

        
        self.face_recognition_auth = FaceRecognitionAuth()
        self.face_recognition_enabled = self.face_recognition_auth.is_enabled()
        
        
        self.salt = b'salt_for_kdf'
        self.encryption_key = None
        self.language = self.load_initial_language()
        self.two_factor_auth = TwoFactorAuth()
        utils.load_settings()
        
        self.load_logo()
        self.load_symbols()
        self.create_sidebar()
        #Loading settings, languages and ect.
        
        # Fonts
        default_font = ("Helvetica", 12)
        self.style.configure('TLabel', font=default_font)
        self.style.configure('TButton', font=default_font)
        self.style.configure('TEntry', font=default_font)
        self.style.configure('TCheckbutton', font=default_font)
        self.style.configure('Treeview', font=default_font,  rowheight=20)
        self.style.configure('Treeview.Heading', font=("Helvetica", 12, "bold"))
        self.style.configure("red.Horizontal.TProgressbar", foreground="red", background="red")
        self.style.configure("orange.Horizontal.TProgressbar", foreground="orange", background="orange")
        self.style.configure("yellow.Horizontal.TProgressbar", foreground="yellow", background="yellow")
        self.style.configure("green.Horizontal.TProgressbar", foreground="green", background="green")

        self.settings_file = "settings.json"
        self.load_settings()
        self.auto_logout = AutoLogout(self.auto_logout_time, self.logout)
        self.auto_logout.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.bind("<Key>", self.reset_auto_logout)
        self.root.bind("<Button-1>", self.reset_auto_logout)
        self.root.bind("<MouseWheel>", self.reset_auto_logout)

        self.lockout_file = os.path.join(os.getenv('APPDATA'), '.wyvern_guard_lockout')
        self.backup_lockout_file = os.path.join(os.getenv('LOCALAPPDATA'), '.wyvern_guard_lockout_backup')
        self.max_attempts = 3
        self.lockout_times = [60, 180, 600, 1800, 3600]  # in seconds
        self.encryption_key = None
        self.lockout_info = self.load_lockout_info()
        self.check_initial_lockout_status()
        self.lockout_label = None
        self.unlock_button = None

        if not os.path.exists("master_password.json"):
            self.create_master_password_screen()
        else:
            self.master_password_screen()

    def load_initial_language(self):
        try:
            if os.path.exists("initial_language.json"):
                with open("initial_language.json", "r") as file:
                    data = json.load(file)
                    return data.get("language", "English")
            else:
                return "English"
        except Exception as e:
            print(f"Error loading initial language preference: {e}")
            return "English"
    
    def save_initial_language(self, language):
        try:
            with open("initial_language.json", "w") as file:
                json.dump({"language": language}, file)
        except Exception as e:
            print(f"Error saving initial language preference: {e}")

    def load_logo(self):
        try:
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Constructs the path to the logo file
            logo_path = os.path.join(current_dir, "wglogo.webp")
            print(f"Attempting to load logo from: {logo_path}")
            
            if not os.path.exists(logo_path):
                print(f"Logo file not found at {logo_path}")
                return

            logo_image = Image.open(logo_path)
            
            
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            # Displays logo
            logo_label = ttk.Label(self.root, image=self.logo_photo)
            logo_label.image = self.logo_photo
            logo_label.pack(pady=10)
            
            self.root.iconphoto(False, self.logo_photo)
            
            print("Logo loaded and displayed successfully")
        except Exception as e:
            print(f"Error loading logo: {e}")

    def load_symbols(self):
        # Define symbols for each button
        self.symbols = {
            'main_menu': '🏠',
            'add_password': '➕',
            'view_passwords': '🔑',
            'secure_notes': '📝',
            'export_passwords': '📤',
            'import_passwords': '📥',
            'settings': '⚙️',
        }

    def initialize_encryption_key(self):
        if os.path.exists("key.key"):
            with open("key.key", "rb") as key_file:
                self.encryption_key = key_file.read()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def save_language_preference(self, language):
        self.save_initial_language(language)  # Saves unencrypted version of language
        if self.encryption_key:
            encrypted_language = encrypt_data(language, self.encryption_key)
            with open("language_preference.txt", "wb") as file:
                file.write(encrypted_language)

    def load_language_after_unlock(self):
        try:
            if os.path.exists("language_preference.txt"):
                with open("language_preference.txt", "rb") as file:
                    encrypted_language = file.read()
                self.language = decrypt_data(encrypted_language, self.encryption_key)
            else:
                self.language = self.load_initial_language()
        except Exception as e:
            print(f"Error loading language preference: {e}")
            self.language = self.load_initial_language()
        
    def change_language(self):
        languages = ["English", "Lithuanian"]
        selected_language = tk.StringVar(value=self.language)
        
        def on_language_change():
            new_language = selected_language.get()
            if new_language != self.language:
                self.language = new_language
                self.save_language_preference(new_language)
                messagebox.showinfo(self.translate("Language Changed"), 
                                    self.translate("Please restart the application for the changes to take effect."))
        
        language_window = tk.Toplevel(self.root)
        language_window.title(self.translate("Change Language"))
        language_window.geometry("300x150")
        self.center_window(300, 150, window=language_window)
        
        ttk.Label(language_window, text=self.translate("Select Language:")).pack(pady=10)
        
        for lang in languages:
            ttk.Radiobutton(language_window, text=lang, variable=selected_language, value=lang).pack()
        
        ttk.Button(language_window, text=self.translate("Apply"), command=on_language_change).pack(pady=10)
        
        
    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            self.auto_logout_time = settings.get('auto_logout_time', 300)
        else:
            self.auto_logout_time = 300
    
    def reset_auto_logout(self, event=None):
        self.auto_logout.reset()
        self.auto_logout.start()

    def logout(self):
        self.encryption_key = None
        self.master_password_screen()

    def create_master_password_screen(self):
        self.clear_screen()
        self.center_window(600, 400)
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text=self.translate("Create Master Password")).pack(pady=10)
        self.new_master_password_entry = ttk.Entry(frame, show="*")
        self.new_master_password_entry.pack(pady=5)
        ttk.Button(frame, text=self.translate("Save"), command=self.save_master_password_and_setup_2fa).pack(pady=5)

    def save_master_password_and_setup_2fa(self):
        master_password = self.new_master_password_entry.get()
        hashed_password = hashlib.sha256(master_password.encode()).hexdigest()
        secret = self.two_factor_auth.generate_secret()
        master_data = {
            "master_password": hashed_password,
            "two_factor_secret": secret
        }
        generate_and_save_key(master_password)
        self.encryption_key = load_key(master_password)
        with open("master_password.json", "w") as file:
            json.dump(master_data, file)
        encrypt_file("master_password.json", self.encryption_key)
        self.save_language_preference(self.language)  # Saves language preference with new encryption key
        self.setup_2fa_screen(secret)

    def load_lockout_info(self):
        lockout_info = self.read_lockout_file(self.lockout_file)
        if lockout_info is None:
            lockout_info = self.read_lockout_file(self.backup_lockout_file)
        
        if lockout_info is None:
            lockout_info = self.read_from_registry()
        
        if lockout_info is None:
            lockout_info = {
                "attempts": 0,
                "lockout_until": None,
                "lockout_count": 0,
                "is_locked": False
            }
        
        # Check if there's an active lockout
        if lockout_info["lockout_until"]:
            lockout_until = datetime.fromisoformat(lockout_info["lockout_until"])
            if datetime.now() < lockout_until:
                lockout_info["is_locked"] = True
            else:
                # Reset if lockout has expired
                lockout_info["lockout_until"] = None
                lockout_info["is_locked"] = False
                lockout_info["attempts"] = 0
                # Note: We don't reset lockout_count here
        
        return lockout_info

    def save_lockout_info(self):
        self.lockout_info['hash'] = self.calculate_hash(self.lockout_info)
        self.write_lockout_file(self.lockout_file)
        self.write_lockout_file(self.backup_lockout_file)
        self.write_to_registry()
    
    def write_lockout_file(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(self.lockout_info, file)

    def read_from_registry(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\WyvernGuard") as key:
                data = winreg.QueryValueEx(key, "LockoutInfo")[0]
                return json.loads(data)
        except WindowsError:
            return None

    def write_to_registry(self):
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\WyvernGuard") as key:
                winreg.SetValueEx(key, "LockoutInfo", 0, winreg.REG_SZ, json.dumps(self.lockout_info))
        except WindowsError:
            pass
    
    def read_lockout_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                lockout_info = json.load(file)
            if self.verify_integrity(lockout_info):
                return lockout_info
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None
    
    def verify_integrity(self, lockout_info):
        if 'hash' not in lockout_info:
            return False
        stored_hash = lockout_info.pop('hash')
        calculated_hash = self.calculate_hash(lockout_info)
        lockout_info['hash'] = stored_hash
        return stored_hash == calculated_hash
    
    def calculate_hash(self, data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def check_initial_lockout_status(self):
        if self.lockout_info["lockout_until"]:
            lockout_until = datetime.fromisoformat(self.lockout_info["lockout_until"])
            if datetime.now() < lockout_until:
                self.lockout_info["is_locked"] = True
                # Set lockout_level to 0 to ensure it starts from 60 seconds
                self.lockout_info["lockout_level"] = 0
            else:
                # Reset lockout if it has expired
                self.reset_lockout()
        else:
            # Ensure lockout_level is 0 even if there's no active lockout
            self.lockout_info["lockout_level"] = 0
        self.save_lockout_info()

    def reset_lockout(self):
        self.lockout_info["lockout_until"] = None
        self.lockout_info["attempts"] = 0
        self.lockout_info["is_locked"] = False
        self.save_lockout_info()

    def master_password_screen(self):
        self.clear_screen()
        self.center_window(800, 500)
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        button_width = 20
        input_width = 30

        ttk.Label(frame, text=self.translate("Enter Master Password")).pack(pady=10)
        self.master_password_entry = ttk.Entry(frame, show="*", width=input_width)
        self.master_password_entry.pack(pady=5)

        self.lockout_label = ttk.Label(frame, text="")
        self.lockout_label.pack(pady=5)

        self.unlock_button = ttk.Button(frame, text=self.translate("Unlock"), command=self.verify_master_password, width=button_width)
        self.unlock_button.pack(pady=5)

        reset_button = ttk.Button(frame, text=self.translate("Reset Master Password"), command=self.reset_master_password, width=button_width)
        reset_button.pack(pady=5)

        self.update_lockout_ui()

    def check_lockout_status(self):
        if self.lockout_info["lockout_until"]:
            lockout_until = datetime.fromisoformat(self.lockout_info["lockout_until"])
            current_time = datetime.now()
            if current_time < lockout_until:
                remaining_time = lockout_until - current_time
                self.update_lockout_ui(remaining_time)
                self.root.after(1000, self.check_lockout_status)
            else:
                self.unlock_button.config(state="normal")
                self.lockout_label.config(text="")
                self.lockout_info["lockout_until"] = None
                self.lockout_info["attempts"] = 0
                self.lockout_info["lockout_level"] = 0
                self.save_lockout_info()

    def update_lockout_ui(self):
        if self.lockout_info.get("is_locked", False):
            lockout_until = datetime.fromisoformat(self.lockout_info["lockout_until"])
            current_time = datetime.now()
            if current_time < lockout_until:
                remaining_time = lockout_until - current_time
                minutes, seconds = divmod(remaining_time.seconds, 60)
                if self.lockout_label:
                    self.lockout_label.config(text=f"Locked out for {minutes:02d}:{seconds:02d}")
                if self.unlock_button:
                    self.unlock_button.config(state="disabled")
                self.root.after(1000, self.update_lockout_ui)
            else:
                self.reset_lockout()
                if self.lockout_label:
                    self.lockout_label.config(text="")
                if self.unlock_button:
                    self.unlock_button.config(state="normal")
        else:
            if self.lockout_label:
                self.lockout_label.config(text="")
            if self.unlock_button:
                self.unlock_button.config(state="normal")

    def setup_2fa_screen(self, secret):
        self.clear_screen()
        self.center_window(450, 500)
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text=self.translate("Set up Two-Factor Authentication"), font=("Helvetica", 14, "bold")).pack(pady=10)
        
        self.qr_instruction_label = ttk.Label(frame, text=self.translate("Scan this QR code with your authenticator app:"), wraplength=350)
        self.qr_instruction_label.pack(pady=5)

        # QR code display
        self.qr_frame = ttk.Frame(frame)
        self.qr_frame.pack(pady=10)

        qr_code = self.two_factor_auth.generate_qr_code(secret, "USB Password Manager User", box_size=3, border=2)
        qr_image = Image.open(BytesIO(base64.b64decode(qr_code)))
        self.qr_photo = ImageTk.PhotoImage(qr_image)
        self.qr_label = ttk.Label(self.qr_frame, image=self.qr_photo)
        self.qr_label.image = self.qr_photo
        self.qr_label.pack()

        # Secret code display (initially hidden)
        self.secret_frame = ttk.Frame(frame)
        self.secret_label = ttk.Label(self.secret_frame, text=self.translate("Enter this code in your authenticator app:"), wraplength=350)
        self.secret_label.pack(pady=5)
        
        # Doesn't work? code display
        self.secret_text = tk.Text(self.secret_frame, height=1, width=40, font=("Courier", 12))
        self.secret_text.insert("1.0", secret)
        self.secret_text.configure(state="disabled")
        self.secret_text.pack(pady=5)

        # ctr + c
        self.secret_text.bind("<Control-c>", lambda e: self.copy_secret())

        # Doesn't work? button
        self.toggle_button = ttk.Button(frame, text=self.translate("Doesn't work?"), command=self.toggle_qr_secret)
        self.toggle_button.pack(pady=5)

        ttk.Label(frame, text=self.translate("Enter the 6-digit code from your authenticator app:"), wraplength=350).pack(pady=5)
        self.verify_2fa_entry = ttk.Entry(frame)
        self.verify_2fa_entry.pack(pady=5)
        ttk.Button(frame, text=self.translate("Verify"), command=self.verify_2fa_setup).pack(pady=5)

    def toggle_qr_secret(self):
        if self.qr_frame.winfo_viewable():
            # Hide QR code and show secret
            self.qr_instruction_label.pack_forget()
            self.qr_frame.pack_forget()
            self.secret_frame.pack(before=self.toggle_button)
            self.toggle_button.config(text=self.translate("Show QR Code"))
        else:
            # Show QR code and hide secret
            self.secret_frame.pack_forget()
            self.qr_instruction_label.pack(before=self.toggle_button)
            self.qr_frame.pack(after=self.qr_instruction_label)
            self.toggle_button.config(text=self.translate("Doesn't work?"))

    def copy_secret(self):
        secret = self.secret_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(secret)
        self.root.update()

    def verify_2fa_setup(self):
        try:
            decrypt_file("master_password.json", self.encryption_key)
            with open("master_password.json", "r") as file:
                file_content = file.read()
                print(f"File content: {file_content}")
                master_data = json.loads(file_content)
            encrypt_file("master_password.json", self.encryption_key)
            
            secret = master_data["two_factor_secret"]
            self.two_factor_auth.totp = self.two_factor_auth.get_totp(secret)
            
            entered_code = self.verify_2fa_entry.get()
            print(f"Entered code: {entered_code}")
            
            if self.two_factor_auth.verify(entered_code):
                messagebox.showinfo(self.translate("Success"), self.translate("Two-Factor Authentication set up successfully!"))
                self.master_password_screen()
            else:
                messagebox.showerror(self.translate("Error"), self.translate("Invalid code. Please try again."))
        except Exception as e: #Printing errors
            error_message = f"{self.translate('An error occurred')}: {str(e)}\n"
            error_message += f"{self.translate('Error type')}: {type(e).__name__}\n"
            error_message += f"{self.translate('File exists')}: {os.path.exists('master_password.json')}\n"
            if os.path.exists('master_password.json'):
                error_message += f"{self.translate('File size')}: {os.path.getsize('master_password.json')} {self.translate('bytes')}\n"
            messagebox.showerror(self.translate("Error"), error_message)
            print(error_message)
            self.master_password_screen()

    def get_device_id(self):
        device_id_file = "device_id.json"
        
        # Checks if ID exists
        if os.path.exists(device_id_file):
            with open(device_id_file, "r") as file:
                try:
                    data = json.load(file)
                    return data["device_id"]
                except (json.JSONDecodeError, KeyError):
                    # If the file is corrupted or doesn't contain the device_id, it will generate a new one
                    pass

        # Generates new ID if it doesn't exist
        device_id = self.generate_device_id()

        # Stores ID
        with open(device_id_file, "w") as file:
            json.dump({"device_id": device_id}, file)

        return device_id

    def generate_device_id(self):
        try:
            import platform
            system_info = platform.uname()
            mac_address = uuid.getnode()
        except:
            # If it can't get system info, use a random UUID
            return str(uuid.uuid4())

        # Creates a unique string based on system information
        unique_string = f"{system_info.system}-{system_info.node}-{system_info.machine}-{mac_address}"

        # Hashes the unique string to get a consistent device ID
        device_id = hashlib.sha256(unique_string.encode()).hexdigest()

        return device_id

    def verify_master_password(self):
        entered_password = self.master_password_entry.get()
        hashed_entered_password = hashlib.sha256(entered_password.encode()).hexdigest()
        
        try:
            self.encryption_key = load_key(entered_password)
            decrypt_file("master_password.json", self.encryption_key)
            with open("master_password.json", "r") as file:
                master_data = json.load(file)
            encrypt_file("master_password.json", self.encryption_key)
            stored_password = master_data["master_password"]
            secret = master_data["two_factor_secret"]

            self.load_lockout_info()
        except (FileNotFoundError, json.JSONDecodeError, cryptography.fernet.InvalidToken):
            self.handle_failed_attempt()
            return

        if hashed_entered_password == stored_password:
            self.lockout_info["attempts"] = 0
            self.lockout_info["lockout_until"] = None
            self.lockout_info["is_locked"] = False
            self.save_lockout_info()
            
            self.load_language_after_unlock()
            device_id = self.get_device_id()
            if self.two_factor_auth.is_device_trusted(device_id):
                if self.face_recognition_enabled:
                    self.face_recognition_check()
                else:
                    self.password_manager_screen()
                    self.auto_logout.start()
            else:
                self.two_factor_auth_screen(secret)
        else:
            self.handle_failed_attempt()
    
    def face_recognition_check(self):
        face_recognition_window = None
        canvas = None
        status_label = None
        cap = None

        def create_window():
            nonlocal face_recognition_window, canvas, status_label
            face_recognition_window = tk.Toplevel(self.root)
            face_recognition_window.title(self.translate("Face Recognition"))
            face_recognition_window.geometry("400x450")
            
            # Center the window
            face_recognition_window.update_idletasks()
            width = face_recognition_window.winfo_width()
            height = face_recognition_window.winfo_height()
            x = (face_recognition_window.winfo_screenwidth() // 2) - (width // 2)
            y = (face_recognition_window.winfo_screenheight() // 2) - (height // 2)
            face_recognition_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

            ttk.Label(face_recognition_window, text=self.translate("Please look at the camera")).pack(pady=10)

            # Create a canvas to display the camera feed
            canvas = tk.Canvas(face_recognition_window, width=320, height=240)
            canvas.pack(pady=10)

            # Add a status label
            status_label = ttk.Label(face_recognition_window, text=self.translate("Initializing camera..."))
            status_label.pack(pady=10)

            # Set up the closing protocol
            face_recognition_window.protocol("WM_DELETE_WINDOW", on_closing)

            return face_recognition_window, canvas, status_label

        def initialize_camera():
            nonlocal cap, face_recognition_window, canvas, status_label
            try:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise ValueError("Failed to open camera")
                
                # Camera is ready, create and show the window
                face_recognition_window, canvas, status_label = create_window()
                face_recognition_window.after(10, update_frame)
            except Exception as e:
                error_message = self.translate("Error: Camera not found or cannot be accessed.")
                messagebox.showerror(self.translate("Camera Error"), error_message)
                print(f"Camera error: {str(e)}")
                self.master_password_screen()

        def update_frame():
            nonlocal cap, face_recognition_window, canvas, status_label
            if not cap or not cap.isOpened():
                status_label.config(text=self.translate("Camera not available. Please try again."))
                return

            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                try:
                    if self.face_recognition_auth.verify_face(frame):
                        status_label.config(text=self.translate("Face recognized!"))
                        cap.release()
                        face_recognition_window.destroy()
                        self.password_manager_screen()
                        self.auto_logout.start()
                        return
                    else:
                        status_label.config(text=self.translate("Face not recognized"))
                except Exception as e:
                    logging.error(f"Error during face verification: {str(e)}")
                    status_label.config(text=self.translate("Error during face recognition"))
                    self.face_recognition_enabled = False
                    cap.release()
                    face_recognition_window.destroy()
                    self.master_password_screen()
                    return

                # Draw rectangle around the face
                face_locations = face_recognition.face_locations(rgb_frame)
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 2)

                # Convert to PhotoImage
                image = Image.fromarray(rgb_frame)
                image = image.resize((320, 240), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image=image)
                
                # Update canvas
                canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                canvas.image = photo  # Keep a reference
            else:
                status_label.config(text=self.translate("Error capturing frame. Please try again."))
            
            face_recognition_window.after(10, update_frame)

        def on_closing():
            nonlocal cap, face_recognition_window
            if cap:
                cap.release()
            if face_recognition_window and face_recognition_window.winfo_exists():
                face_recognition_window.destroy()
            self.master_password_screen()

        # Start the camera initialization process
        initialize_camera()

    def skip_face_recognition(self, window):
        window.destroy()
        self.password_manager_screen()
        self.auto_logout.start()

    def get_current_lockout_duration(self):
        lockout_count = self.lockout_info.get("lockout_count", 0)
        index = min(lockout_count, len(self.lockout_times) - 1)
        return self.lockout_times[index]

    def handle_failed_attempt(self):
        self.lockout_info["attempts"] += 1
        
        if self.lockout_info["attempts"] >= self.max_attempts:
            self.lockout_info["lockout_count"] += 1
            lockout_duration = self.get_current_lockout_duration()
            self.lockout_info["lockout_until"] = (datetime.now() + timedelta(seconds=lockout_duration)).isoformat()
            self.lockout_info["attempts"] = 0
            self.lockout_info["is_locked"] = True
            
            messagebox.showerror(self.translate("Error"), 
                                self.translate(f"Too many failed attempts. Locked out for {lockout_duration // 60} minutes."))
            
            self.save_lockout_info()
            self.update_lockout_ui()
        else:
            remaining_attempts = self.max_attempts - self.lockout_info["attempts"]
            messagebox.showerror(self.translate("Error"), 
                                self.translate(f"Incorrect master password. {remaining_attempts} attempts remaining."))
        
        self.save_lockout_info()
    
    def handle_failed_attempt(self):
        self.lockout_info["attempts"] += 1
        
        if self.lockout_info["attempts"] >= self.max_attempts:
            # Increment lockout_level only if it's a new lockout session
            if not self.lockout_info["is_locked"]:
                self.lockout_info["lockout_level"] = 0
            lockout_duration = self.lockout_times[self.lockout_info["lockout_level"]]
            self.lockout_info["lockout_until"] = (datetime.now() + timedelta(seconds=lockout_duration)).isoformat()
            self.lockout_info["attempts"] = 0
            self.lockout_info["is_locked"] = True
            
            messagebox.showerror(self.translate("Error"), 
                                 self.translate(f"Too many failed attempts. Locked out for {lockout_duration // 60} minutes."))
            
            # Increment lockout_level for next time, but cap it at the maximum
            self.lockout_info["lockout_level"] = min(self.lockout_info["lockout_level"] + 1, len(self.lockout_times) - 1)
            
            self.save_lockout_info()
            self.update_lockout_ui()
        else:
            remaining_attempts = self.max_attempts - self.lockout_info["attempts"]
            messagebox.showerror(self.translate("Error"), 
                                 self.translate(f"Incorrect master password. {remaining_attempts} attempts remaining."))
        
        self.save_lockout_info()

    def two_factor_auth_screen(self, secret):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text=self.translate("Two-Factor Authentication")).pack(pady=10)
        ttk.Label(frame, text=self.translate("Enter the 6-digit code from your authenticator app:")).pack(pady=5)
        self.two_factor_entry = ttk.Entry(frame)
        self.two_factor_entry.pack(pady=5)

        trust_frame = ttk.Frame(frame)
        trust_frame.pack(pady=10)

        self.trust_device_var = tk.BooleanVar()
        trust_checkbox = ttk.Checkbutton(trust_frame, text=self.translate("Trust this device for"), variable=self.trust_device_var)
        trust_checkbox.pack(side="left")

        self.trust_duration_var = tk.StringVar()
        self.trust_duration_options = [
            ("1", self.translate("1 day")),
            ("3", self.translate("3 days")),
            ("10", self.translate("10 days")),
            ("30", self.translate("30 days"))
        ]
        trust_duration_menu = ttk.Combobox(trust_frame, textvariable=self.trust_duration_var, 
                                        values=[option[1] for option in self.trust_duration_options], 
                                        state="readonly", width=10)
        trust_duration_menu.set(self.trust_duration_options[0][1])
        trust_duration_menu.pack(side="left", padx=5)

        ttk.Button(frame, text=self.translate("Verify"), command=lambda: self.verify_2fa(secret, self.trust_duration_options if hasattr(self, 'trust_duration_options') else None)).pack(pady=5)

    def verify_2fa(self, secret, trust_duration_options=None):
        self.two_factor_auth.totp = self.two_factor_auth.get_totp(secret)
        if self.two_factor_auth.verify(self.two_factor_entry.get()):
            if self.trust_device_var.get() and trust_duration_options:
                duration_map = {"1": 1, "3": 3, "10": 10, "30": 30}
                selected_duration = next(key for key, value in trust_duration_options if value == self.trust_duration_var.get())
                duration_days = duration_map[selected_duration]
                device_id = self.get_device_id()
                self.two_factor_auth.trust_device(device_id, duration_days)
            if self.face_recognition_enabled:
                self.face_recognition_check()
            else:
                self.password_manager_screen()
                self.auto_logout.start()
        else:
            messagebox.showerror(self.translate("Error"), self.translate("Invalid code. Please try again."))

    def unlock(self):
        entered_password = self.master_password_entry.get()
        hashed_entered_password = hashlib.sha256(entered_password.encode()).hexdigest()
        try:
            with open("master_password.json", "r") as file:
                master_data = json.load(file)
                stored_password = master_data["master_password"]
        except FileNotFoundError:
            messagebox.showerror(self.translate("Error"), self.translate("Master password file not found"))
            return
        except json.JSONDecodeError:
            messagebox.showerror(self.translate("Error"), self.translate("Invalid master password file"))
            return

        if hashed_entered_password == stored_password:
            self.encryption_key = derive_key(entered_password, self.salt)
            self.password_manager_screen()
            self.auto_logout.start()
        else:
            messagebox.showerror(self.translate("Error"), self.translate("Incorrect master password"))

    def reset_master_password(self):
        if messagebox.askyesno(self.translate("Reset Master Password"), 
                self.translate("This will delete all stored information including passwords and it will reset the master password. Are you sure?")):
            
            files_to_remove = [
                "master_password.json",
                "passwords.json",
                "device_id.json",
                "trusted_devices.json",
                "secure_notes.json",
                "key.key",
                "salt.bin",
                "adjectives.json",
                "nouns.json",
                "categories.json",
                'face_recognition_settings.json'
            ]

            for file in files_to_remove:
                if os.path.exists(file):
                    os.remove(file)
            
            messagebox.showinfo(self.translate("Info"), self.translate("All passwords have been deleted and master password has been reset."))
            
            # Recreates the encryption key
            self.encryption_key = Fernet.generate_key()
            with open("key.key", "wb") as key_file:
                key_file.write(self.encryption_key)
            
            self.create_master_password_screen()

    def password_manager_screen(self):
        self.navigation_history.clear()
        self.navigation_history.append('password_manager')
        self.clear_screen()
        self.center_window(1600, 700)  # Increased window size to accommodate sidebar

        # Configure button styles
        self.configure_button_styles()

        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar frame
        self.sidebar_frame = ttk.Frame(main_frame, width=250, style='Sidebar.TFrame')
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sidebar toggle button
        self.sidebar_expanded = True
        self.toggle_button = ttk.Button(self.sidebar_frame, text='◀', command=self.toggle_sidebar, style='Toggle.TButton')
        self.toggle_button.pack(anchor='ne', padx=5, pady=5)

        # Sidebar buttons
        self.load_symbols()

        self.sidebar_expanded = True
        self.style.configure("Sidebar.TButton", 
                            font=("Helvetica", 12), 
                            padding=10,
                            background="#2c2c2c",  # Dark background
                            foreground="white")    # White text
        
        self.style.map("Sidebar.TButton",
                    background=[('active', '#3c3c3c')],  # Slightly lighter when active
                    foreground=[('active', 'white')])

        # Create sidebar buttons
        self.create_sidebar_button('main_menu', self.translate('Main Menu'), lambda: self.update_content('password_manager'), "Sidebar.TButton")
        self.create_sidebar_button('add_password', self.translate('Add Password'), lambda: self.update_content('add_password'), "Sidebar.TButton")
        self.create_sidebar_button('view_passwords', self.translate('View Passwords'), lambda: self.update_content('view_passwords'), "Sidebar.TButton")
        self.create_sidebar_button('secure_notes', self.translate('Secure Notes'), lambda: self.update_content('secure_notes'), "Sidebar.TButton")
        self.create_sidebar_button('export_passwords', self.translate('Export Passwords'), lambda: self.update_content('export_passwords'), "Sidebar.TButton")
        self.create_sidebar_button('import_passwords', self.translate('Import Passwords'), lambda: self.update_content('import_passwords'), "Sidebar.TButton")
        self.create_sidebar_button('settings', self.translate('Settings'), lambda: self.update_content('settings'), "Sidebar.TButton")

        # Initial content
        self.update_content('password_manager')

        self.auto_logout.reset()
        self.auto_logout.start()
    

    def default_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Welcome to WyvernGuard'), font=("Helvetica", 24, "bold")).pack(pady=(0, 20))

        # Create a scrolled text widget
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Helvetica", 12))
        text_widget.pack(expand=True, fill="both")

        # Use the current language setting from the class instance
        current_language = self.language

        # Set the appropriate manual file based on language
        if current_language == "Lithuanian":
            manual_file = "user_manual_lt.md"
        else:
            manual_file = "user_manual_en.md"

        # Get the correct path to the manual file
        manual_file_path = get_resource_path(manual_file)

        # Load the Markdown content
        try:
            with open(manual_file_path, "r", encoding="utf-8") as md_file:
                md_content = md_file.read()
            
            # Insert the Markdown content with enhanced formatting
            in_code_block = False
            in_list = False
            for line in md_content.split('\n'):
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    text_widget.insert(tk.END, line + '\n', 'code')
                    continue
                
                if in_code_block:
                    text_widget.insert(tk.END, line + '\n', 'code')
                    continue

                if line.startswith('# '):
                    text_widget.insert(tk.END, line[2:] + '\n', 'h1')
                elif line.startswith('## '):
                    text_widget.insert(tk.END, line[3:] + '\n', 'h2_center')
                elif line.startswith('### '):
                    text_widget.insert(tk.END, line[4:] + '\n', 'h3')
                elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                    number, content = line.split('.', 1)
                    text_widget.insert(tk.END, f"{number}.", 'list_number')
                    content = content.strip()
                    if content.startswith('**') and content.endswith('**'):
                        text_widget.insert(tk.END, f" {content[2:-2]}\n", 'list_bold')
                    else:
                        text_widget.insert(tk.END, f" {content}\n", 'list')
                    in_list = True
                elif line.startswith('- ') or line.startswith('* '):
                    text_widget.insert(tk.END, '  • ' + line[2:] + '\n', 'list')
                    in_list = True
                elif in_list and line.strip() == '':
                    text_widget.insert(tk.END, '\n')
                    in_list = False
                else:
                    # Handle inline formatting
                    line = re.sub(r'\*\*(.*?)\*\*', lambda m: text_widget.tag_add('bold', text_widget.index(tk.INSERT), text_widget.index(f"{tk.INSERT}+{len(m.group(1))}c")) or m.group(1), line)
                    line = re.sub(r'\*(.*?)\*', lambda m: text_widget.tag_add('italic', text_widget.index(tk.INSERT), text_widget.index(f"{tk.INSERT}+{len(m.group(1))}c")) or m.group(1), line)
                    line = re.sub(r'`(.*?)`', lambda m: text_widget.tag_add('inline_code', text_widget.index(tk.INSERT), text_widget.index(f"{tk.INSERT}+{len(m.group(1))}c")) or m.group(1), line)
                    text_widget.insert(tk.END, line + '\n')
            
            # Configure tags for formatting
            text_widget.tag_configure('h1', font=("Helvetica", 20, "bold"))
            text_widget.tag_configure('h2_center', font=("Helvetica", 18, "bold"), justify='center')
            text_widget.tag_configure('h3', font=("Helvetica", 16, "bold"))
            text_widget.tag_configure('list', lmargin1=20, lmargin2=40)
            text_widget.tag_configure('list_number', lmargin1=20, lmargin2=40)
            text_widget.tag_configure('list_bold', lmargin1=20, lmargin2=40, font=("Helvetica", 12, "bold"))
            text_widget.tag_configure('code', font=("Courier", 12), background="#f0f0f0")
            text_widget.tag_configure('bold', font=("Helvetica", 12, "bold"))
            text_widget.tag_configure('italic', font=("Helvetica", 12, "italic"))
            text_widget.tag_configure('inline_code', font=("Courier", 12), background="#f0f0f0")
            
        except FileNotFoundError:
            text_widget.insert(tk.END, self.translate("User manual file not found."))
            text_widget.insert(tk.END, f"\nAttempted to open: {manual_file_path}")
        except Exception as e:
            text_widget.insert(tk.END, f"{self.translate('Error loading user manual')}: {str(e)}")
            text_widget.insert(tk.END, f"\nAttempted to open: {manual_file_path}")

        self.auto_logout.reset()
        self.auto_logout.start()

    def create_sidebar(self):
        self.sidebar_frame = ttk.Frame(self.root, width=250, style='Sidebar.TFrame')
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        self.sidebar_expanded = True
        self.toggle_button = ttk.Button(self.sidebar_frame, text='◀', command=self.toggle_sidebar, style='Toggle.TButton')
        self.toggle_button.pack(anchor='ne', padx=5, pady=5)

        button_style = "Sidebar.TButton"
        self.style.configure(button_style, font=("Helvetica", 12), padding=10)

        self.create_sidebar_button('main_menu', 'Main Menu', lambda: self.update_content('password_manager'), button_style)
        self.create_sidebar_button('add_password', 'Add Password', lambda: self.update_content('add_password'), button_style)
        self.create_sidebar_button('view_passwords', 'View Passwords', lambda: self.update_content('view_passwords'), button_style)
        self.create_sidebar_button('secure_notes', 'Secure Notes', lambda: self.update_content('secure_notes'), button_style)
        self.create_sidebar_button('export_passwords', 'Export Passwords', lambda: self.update_content('export_passwords'), button_style)
        self.create_sidebar_button('import_passwords', 'Import Passwords', lambda: self.update_content('import_passwords'), button_style)
        self.create_sidebar_button('settings', 'Settings', lambda: self.update_content('settings'), button_style)

    def create_sidebar_button(self, symbol_key, text, command, style):
        var = tk.StringVar()
        var.set(f"{self.symbols[symbol_key]} {self.translate(text)}")
        button = ttk.Button(self.sidebar_frame, textvariable=var, command=command, style=style)
        button.pack(fill=tk.X, padx=5, pady=2)
        self.sidebar_buttons.append((button, text, symbol_key))
        self.button_vars[symbol_key] = var

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.collapse_sidebar()
        else:
            self.expand_sidebar()
        self.sidebar_expanded = not self.sidebar_expanded

    def collapse_sidebar(self):
        self.sidebar_frame.config(width=60)
        self.toggle_button.config(text='▶')
        for _, _, symbol_key in self.sidebar_buttons:
            self.button_vars[symbol_key].set(self.symbols[symbol_key])

    def expand_sidebar(self):
        self.sidebar_frame.config(width=250)
        self.toggle_button.config(text='◀')
        for _, text, symbol_key in self.sidebar_buttons:
            self.button_vars[symbol_key].set(f"{self.symbols[symbol_key]} {self.translate(text)}")

    def update_content(self, content_type, *args):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Update content based on selection
        if content_type == 'add_password':
            self.add_password_content()
        elif content_type == 'view_passwords':
            self.view_passwords_content()
        elif content_type == 'edit_password':
            stored_values = args[0] if args else None
            self.edit_password_content(stored_values)
        elif content_type == 'secure_notes':
            self.secure_notes_content()
        elif content_type == 'export_passwords':
            self.export_passwords_content()
        elif content_type == 'import_passwords':
            self.import_passwords_content()
        elif content_type == 'settings':
            self.settings_content()
        elif content_type == 'password_generator':
            self.password_generator_content()
        elif content_type == 'username_generator_settings':
            self.username_generator_settings_content()
        elif content_type == 'categories':
            self.categories_content()
        elif content_type == 'auto_logout':
            self.auto_logout_content()
        elif content_type == 'password_manager':
            self.default_content()
        else:
            self.default_content()

    def configure_button_styles(self):
        self.style.configure('Toggle.TButton', font=('Helvetica', 10))
        self.style.map('Toggle.TButton',
                    background=[('!active', '#2c2c2c'), ('active', '#3c3c3c')],
                    foreground=[('!active', 'white'), ('active', 'white')])

    def handle_navigation(self, screen_name):
        if screen_name == 'add_password':
            self.add_password_screen()
        elif screen_name == 'edit_password':
            self.edit_password_screen()
        elif screen_name == 'settings':
            self.settings_screen()
        else:
            self.password_manager_screen()
    
    def toggle_password_visibility_in_tree(self, item):
        values = self.tree.item(item, 'values')
        tags = self.tree.item(item, 'tags')
        
        if values[3] == "*" * 8:  # If password is hidden
            encrypted_password = tags[0]
            decrypted_password = decrypt_data(encrypted_password.encode(), self.encryption_key)
            new_values = values[:3] + (decrypted_password,) + values[4:-1] + ("🔒",)
        else:  # If password is visible
            new_values = values[:3] + ("*" * 8,) + values[4:-1] + ("👁",)
        
        self.tree.item(item, values=new_values)

    def handle_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if region == "cell":
            if column == "#1":  # Checkbox column
                self.toggle_checkbox(event)
            elif column == "#8":  # Reveal column
                self.toggle_password_visibility_in_tree(item)
        elif region == "heading" and column == "#2":  # Site column header
            self.on_double_click(event)

    def toggle_theme(self):
        new_theme = 'pulse' if self.theme == 'darkly' else 'darkly'
        self.theme = new_theme
        self.style.theme_use(self.theme)
        self.configure_styles() 
        self.save_theme_preference()
        self.settings_content()

    def load_theme_preference(self):
        try:
            with open('theme_preference.json', 'r') as f:
                data = json.load(f)
                return data.get('theme', 'darkly')
        except FileNotFoundError:
            return 'darkly'

    def save_theme_preference(self):
        with open('theme_preference.json', 'w') as f:
            json.dump({'theme': self.theme}, f)

    def configure_button_styles(self):
        self.style.configure('Toggle.TButton', font=('Helvetica', 10))
        self.style.map('Toggle.TButton',
                       background=[('!active', '#2c2c2c'), ('active', '#3c3c3c')],
                       foreground=[('!active', 'white'), ('active', 'white')])

    def translate(self, text): #Perkelt i JSON
        return translations[self.language].get(text, text)

    def change_language(self, new_language):
        self.language = new_language
        self.save_language_preference(new_language)
        
        # Update sidebar button labels
        for button, text, symbol_key in self.sidebar_buttons:
            new_text = f"{self.symbols[symbol_key]} {self.translate(text)}"
            self.button_vars[symbol_key].set(new_text)
        
        # Refresh the settings content
        self.settings_content()

    def export_passwords_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Export Passwords'), font=("Helvetica", 20, "bold")).pack(pady=20)

        # Create a centered frame for buttons
        centered_frame = ttk.Frame(frame)
        centered_frame.pack(expand=True)

        button_frame = ttk.Frame(centered_frame)
        button_frame.pack()

        button_style = "large.TButton"
        button_width = 20

        csv_button = ttk.Button(button_frame, text=self.translate('Export to CSV'), 
                command=self.export_passwords_to_csv, 
                style=button_style, 
                bootstyle=WARNING,
                width=button_width)
        csv_button.pack(side=LEFT, padx=5)

        img_button = ttk.Button(button_frame, text=self.translate('Export as Image'), 
                command=self.export_passwords_as_image, 
                style=button_style, 
                bootstyle=INFO,
                width=button_width)
        img_button.pack(side=LEFT, padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()

    def import_passwords_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Import Passwords'), font=("Helvetica", 20, "bold")).pack(pady=20)

        # Create a centered frame for buttons
        centered_frame = ttk.Frame(frame)
        centered_frame.pack(expand=True)

        button_frame = ttk.Frame(centered_frame)
        button_frame.pack()

        button_style = "large.TButton"
        button_width = 20

        csv_button = ttk.Button(button_frame, text=self.translate('Import from CSV'), 
                command=self.import_passwords_from_csv, 
                style=button_style, 
                bootstyle=WARNING,
                width=button_width)
        csv_button.pack(side=LEFT, padx=5)

        img_button = ttk.Button(button_frame, text=self.translate('Import from Image'), 
                command=self.import_passwords_from_image, 
                style=button_style, 
                bootstyle=INFO,
                width=button_width)
        img_button.pack(side=LEFT, padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()
        
    def encode_data_in_image(self, image_path, data):
        with Image.open(image_path) as img:
            # Converts image to RGB if it's not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            encoded = img.copy()
            width, height = encoded.size
            index = 0

            binary = ''.join(format(ord(i), '08b') for i in data)
            binary += '00000000' 
            data_len = len(binary)
            
            for row in range(height):
                for col in range(width):
                    if index < data_len:
                        pixel = list(encoded.getpixel((col, row)))
                        for color_channel in range(3):  # R, G, B
                            if index < data_len:
                                pixel[color_channel] = pixel[color_channel] & ~1 | int(binary[index])
                                index += 1
                        encoded.putpixel((col, row), tuple(pixel))
                    else:
                        break
                if index >= data_len:
                    break
            
            return encoded
        

    def decode_data_from_image(self, image):
        width, height = image.size
        binary = ''
        
        for row in range(height):
            for col in range(width):
                pixel = image.getpixel((col, row))
                for color_channel in range(3):  # R, G, B
                    binary += str(pixel[color_channel] & 1)
                    if len(binary) % 8 == 0:
                        if binary[-8:] == '00000000':
                            return ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary)-8, 8))
        
        return ''

    def export_passwords_as_image(self):
        if not os.path.exists("passwords.json"):
            messagebox.showinfo(self.translate("Info"), self.translate("No passwords to export"))
            return

        warning_message = self.translate("Warning: This will hide your passwords inside an existing image file. "
                                        "While the data is concealed, it's not encrypted within the image. "
                                        "Keep this image secure. Do you want to continue?")
        
        if not messagebox.askyesno(self.translate("Security Warning"), warning_message, icon='warning'):
            return

        input_image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")],
                                                    title=self.translate("Select Image to Hide Data In"))
        if not input_image_path:
            return

        output_image_path = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG files", "*.png")],
            title=self.translate("Save Output Image"),
            initialfile="exported_passwords.png"
        )
        if not output_image_path:
            return

        try:
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as json_file:
                passwords = json.load(json_file)
            encrypt_file("passwords.json", self.encryption_key)

            # Decrypt passwords before encoding
            for password in passwords:
                decrypted_password = decrypt_data(password['current_password'].encode(), self.encryption_key)
                password['current_password'] = decrypted_password

            passwords_str = json.dumps(passwords)
            encoded_data = base64.b64encode(passwords_str.encode()).decode()
            
            secret_img = self.encode_data_in_image(input_image_path, encoded_data)
            
            secret_img.save(output_image_path, 'PNG')

            messagebox.showinfo(self.translate("Success"), 
                                self.translate("Passwords hidden successfully in the image."))
        except Exception as e:
            messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to hide passwords in image')}: {str(e)}")

    def import_passwords_from_image(self):
        warning_message = self.translate("Warning: This will attempt to extract hidden passwords from an image file. "
                                        "Make sure the image is from a trusted source and contains valid password data. "
                                        "This action cannot be undone. Do you want to continue?")
        
        if not messagebox.askyesno(self.translate("Import Warning"), warning_message, icon='warning'):
            return

        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")],
                                            title=self.translate("Select Image File to Import From"))
        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                hidden_data = self.decode_data_from_image(img)
            
            if not hidden_data:
                raise ValueError("No hidden data found in the image.")

            decoded_data = base64.b64decode(hidden_data).decode()
            imported_passwords = json.loads(decoded_data)

            if os.path.exists("passwords.json"):
                decrypt_file("passwords.json", self.encryption_key)
                with open("passwords.json", "r") as file:
                    existing_passwords = json.load(file)
            else:
                existing_passwords = []

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            imported_count = 0
            skipped_count = 0

            for new_password in imported_passwords:
                # Re-encrypt the password with the current encryption key
                try:
                    re_encrypted_password = encrypt_data(new_password['current_password'], self.encryption_key).decode()
                    new_password['current_password'] = re_encrypted_password
                    
                    # Update the timestamps to current time
                    new_password['history'] = [{
                        "password": re_encrypted_password,
                        "date": current_time,
                        "site": new_password['site'],
                        "username": new_password['username']
                    }]
                    
                except Exception as e:
                    self.logger.error(f"Failed to re-encrypt password for {new_password['site']}: {str(e)}")
                    skipped_count += 1
                    continue

                if any(entry['site'] == new_password['site'] and 
                    entry['username'] == new_password['username']
                    for entry in existing_passwords):
                    skipped_count += 1
                else:
                    existing_passwords.append(new_password)
                    imported_count += 1

            with open("passwords.json", "w") as file:
                json.dump(existing_passwords, file, indent=2)
            encrypt_file("passwords.json", self.encryption_key)

            messagebox.showinfo(
                self.translate("Success"), 
                self.translate("Successfully imported {0} passwords from the image. Skipped {1} entries due to duplicates or encryption issues.").format(imported_count, skipped_count)
            )
            
            if hasattr(self, 'tree'):
                self.load_passwords()

        except Exception as e:
            messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to import passwords from image')}: {str(e)}")

        self.view_passwords_content()
        self.check_expired_passwords() 

    def export_passwords_to_csv(self):
        if not os.path.exists("passwords.json"):
            messagebox.showinfo(self.translate("Info"), self.translate("No passwords to export"))
            return

        warning_message = self.translate("Warning: This will create a CSV file with all your passwords in plain text. "
                                        "This file will not be encrypted and can be read by anyone who has access to it. "
                                        "Please ensure you delete this file after importing it into your browser. "
                                        "Do you want to continue?")
        
        if not messagebox.askyesno(self.translate("Security Warning"), warning_message, icon='warning'):
            return 

        default_filename = f"my_csv_file.csv" #f"password_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=self.translate("Save CSV File"),
            initialfile=default_filename
        )
        if not file_path:
            return  # User cancelled the file dialog

        try:
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as json_file, open(file_path, "w", newline='') as csv_file:
                passwords = json.load(json_file)
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["url", "username", "password"])

                for entry in passwords:
                    site = entry["site"]
                    username = entry["username"]
                    encrypted_password = entry["current_password"]
                    decrypted_password = decrypt_data(encrypted_password.encode(), self.encryption_key)
                    csv_writer.writerow([site, username, decrypted_password])
            encrypt_file("passwords.json", self.encryption_key)

            messagebox.showinfo(self.translate("Success"), 
                                self.translate("Passwords exported successfully. "
                                            "Please remember to delete the CSV file after importing."))
        except Exception as e:
            messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to export passwords')}: {str(e)}")
    
    def import_passwords_from_csv(self):
        warning_message = self.translate("Warning: This will import passwords from a CSV file. "
                                        "Make sure the CSV file is from a trusted source. "
                                        "The importer will look for 'url', 'username', and 'password' columns. "
                                        "This action cannot be undone. Do you want to continue?")
        
        if not messagebox.askyesno(self.translate("Import Warning"), warning_message, icon='warning'):
            return  # User chose not to continue

        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")],
                                            title=self.translate("Select CSV File to Import"))
        if not file_path:
            return  # User cancelled the file dialog

        try:
            imported_count = 0
            skipped_count = 0
            passwords = []
            if os.path.exists("passwords.json"):
                decrypt_file("passwords.json", self.encryption_key)
                with open("passwords.json", "r") as json_file:
                    passwords = json.load(json_file)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(file_path, "r", newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                
                # Checks if required columns are present
                required_columns = {'url', 'username', 'password'}
                csv_columns = set(csv_reader.fieldnames)
                if not required_columns.issubset(csv_columns):
                    missing_columns = required_columns - csv_columns
                    raise ValueError(self.translate(f"Missing required columns: {', '.join(missing_columns)}"))

                for row in csv_reader:
                    site = row['url']
                    username = row['username']
                    password = row['password']

                    # Skips empty rows
                    if not (site.strip() and username.strip() and password.strip()):
                        continue

                    # Checks if this entry already exists
                    if any(entry['site'] == site and 
                        entry['username'] == username and 
                        decrypt_data(entry['current_password'].encode(), self.encryption_key) == password
                        for entry in passwords):
                        skipped_count += 1
                        continue

                    encrypted_password = encrypt_data(password, self.encryption_key)
                
                    new_entry = {
                        "site": site,
                        "username": username,
                        "current_password": encrypted_password.decode(),
                        "history": [{
                            "password": encrypted_password.decode(),
                            "date": current_time,
                            "site": site,
                            "username": username
                        }]
                    }
                    
                    passwords.append(new_entry)
                    imported_count += 1

            with open("passwords.json", "w") as json_file:
                json.dump(passwords, json_file, indent=2)
            encrypt_file("passwords.json", self.encryption_key)

            messagebox.showinfo(
                self.translate("Success"), 
                self.translate("Successfully imported {0} passwords. Skipped {1} duplicate entries.").format(imported_count, skipped_count)
            )
            
            if hasattr(self, 'tree'):
                self.load_passwords()

        except Exception as e:
            messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to import passwords')}: {str(e)}")

        self.view_passwords_content()
        self.check_expired_passwords()

    def secure_notes_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Secure Notes'), font=("Helvetica", 24, "bold")).pack(pady=20)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text=self.translate("Search:")).pack(side="left", padx=(0, 5))
        self.notes_search_entry = ttk.Entry(search_frame)
        self.notes_search_entry.pack(side="left", expand=True, fill="x")
        self.notes_search_entry.bind("<KeyRelease>", self.search_notes)

        content_frame = ttk.Frame(frame)
        content_frame.pack(expand=True, fill="both")

        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(side="left", expand=True, fill="both", padx=(0, 10))

        columns = ("Title", "Date Added")
        self.notes_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            self.notes_tree.heading(col, text=self.translate(col))
            self.notes_tree.column(col, width=150, anchor="center")

        tree_vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.notes_tree.yview)
        self.notes_tree.configure(yscrollcommand=tree_vsb.set)

        self.notes_tree.grid(column=0, row=0, sticky='nsew')
        tree_vsb.grid(column=1, row=0, sticky='ns')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        note_content_frame = ttk.Frame(content_frame)
        note_content_frame.pack(side="right", expand=True, fill="both")

        self.title_entry = ttk.Entry(note_content_frame, width=50)
        self.title_entry.pack(pady=(0, 5), fill="x")
        self.title_entry.config(state="disabled")

        self.note_content_text = scrolledtext.ScrolledText(note_content_frame, wrap=tk.WORD, width=40, height=15)
        self.note_content_text.pack(expand=True, fill="both")
        self.note_content_text.config(state=tk.DISABLED)

        self.load_notes()

        self.notes_tree.bind("<<TreeviewSelect>>", self.display_selected_note)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.translate('Add Note'), command=self.add_note_screen, style="large.TButton", bootstyle=SUCCESS).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text=self.translate("Delete Selected"), command=self.delete_selected_note, style="large.TButton", bootstyle=DANGER).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text=self.translate("Edit Selected"), command=self.edit_selected_note, style="large.TButton", bootstyle=INFO).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text=self.translate("Import"), command=self.import_note, style="large.TButton", bootstyle=WARNING).pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text=self.translate("Export"), command=self.export_note, style="large.TButton", bootstyle=WARNING).pack(side=LEFT, padx=10)

        self.auto_logout.reset()
        self.auto_logout.start()
    
    def import_note(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")], title=self.translate("Select a text file to import"))
        if file_path:
            # Check if the file has a .txt extension
            if not file_path.lower().endswith('.txt'):
                messagebox.showerror(self.translate("Error"), self.translate("Only .txt files are allowed"))
                return

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                title = os.path.splitext(os.path.basename(file_path))[0]
                encrypted_content = encrypt_data(content, self.encryption_key)
                date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_note = {
                    "title": title,
                    "content": encrypted_content.decode(),
                    "date_added": date_added
                }

                notes = []
                if os.path.exists("secure_notes.json"):
                    decrypt_file("secure_notes.json", self.encryption_key)
                    with open("secure_notes.json", "r") as file:
                        notes = json.load(file)
                    encrypt_file("secure_notes.json", self.encryption_key)

                notes.append(new_note)

                with open("secure_notes.json", "w") as file:
                    json.dump(notes, file, indent=2)
                encrypt_file("secure_notes.json", self.encryption_key)

                messagebox.showinfo(self.translate("Success"), self.translate("Note imported successfully"))
                self.load_notes()
            except Exception as e:
                messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to import note')}: {str(e)}")

    def export_note(self):
        selected_items = self.notes_tree.selection()
        if not selected_items:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a note to export"))
            return

        item = selected_items[0]
        note_title = self.notes_tree.item(item, "values")[0]

        decrypt_file("secure_notes.json", self.encryption_key)
        with open("secure_notes.json", "r") as file:
            notes = json.load(file)
        encrypt_file("secure_notes.json", self.encryption_key)

        selected_note = next((note for note in notes if note["title"] == note_title), None)
        if not selected_note:
            messagebox.showerror(self.translate("Error"), self.translate("Failed to find the selected note"))
            return

        decrypted_content = decrypt_data(selected_note['content'].encode(), self.encryption_key)

        # Opens file dialog with pre-filled filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"{note_title}.txt",
            title=self.translate("Export Note")
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(decrypted_content)
                messagebox.showinfo(self.translate("Success"), self.translate("Note exported successfully"))
            except Exception as e:
                messagebox.showerror(self.translate("Error"), f"{self.translate('Failed to export note')}: {str(e)}")

    def edit_selected_note(self):
        selected_items = self.notes_tree.selection()
        if not selected_items:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a note to edit"))
            return

        # Checks if user is already in edit mode
        if hasattr(self, 'edit_mode') and self.edit_mode:
            self.finish_editing()
            return

        self.edit_mode = True
        item = selected_items[0]
        self.current_note_title = self.notes_tree.item(item, "values")[0]

        self.title_entry.config(state="normal")
        self.note_content_text.config(state=tk.NORMAL)
        
        self.title_entry.config(cursor="xterm")
        self.note_content_text.config(cursor="xterm")
        

        self.notes_tree.unbind("<<TreeviewSelect>>")
        self.notes_tree.unbind("<Double-1>")

        self.edit_frame = ttk.Frame(self.root)
        self.edit_frame.pack(pady=10)

        ttk.Button(self.edit_frame, text=self.translate("Save"), command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.edit_frame, text=self.translate("Discard"), command=self.discard_changes).pack(side=tk.LEFT, padx=5)


    def save_changes(self):
            new_title = self.title_entry.get()
            new_content = self.note_content_text.get("1.0", tk.END).strip()

            decrypt_file("secure_notes.json", self.encryption_key)
            with open("secure_notes.json", "r") as file:
                notes = json.load(file)

            for note in notes:
                if note["title"] == self.current_note_title:
                    note["title"] = new_title
                    note["content"] = encrypt_data(new_content, self.encryption_key).decode()
                    break

            with open("secure_notes.json", "w") as file:
                json.dump(notes, file, indent=2)
            encrypt_file("secure_notes.json", self.encryption_key)

            messagebox.showinfo(self.translate("Info"), self.translate("Note updated"))
            self.load_notes()
            self.finish_editing()

    def discard_changes(self):
            self.finish_editing()    

    def finish_editing(self):
        self.edit_mode = False
        if hasattr(self, 'edit_frame'):
            self.edit_frame.destroy()
        self.title_entry.config(state="disabled")
        self.note_content_text.config(state=tk.DISABLED)
        self.title_entry.config(cursor="")
        self.note_content_text.config(cursor="")
        self.notes_tree.bind("<<TreeviewSelect>>", self.display_selected_note)
        self.notes_tree.bind("<Double-1>", self.display_selected_note)
        self.display_selected_note(None)  

    def display_selected_note(self, event):
        selected_items = self.notes_tree.selection()
        if not selected_items:
            self.title_entry.config(state="normal")
            self.title_entry.delete(0, tk.END)
            self.title_entry.config(state="disabled")
            self.note_content_text.config(state=tk.NORMAL)
            self.note_content_text.delete('1.0', tk.END)
            self.note_content_text.config(state=tk.DISABLED)
            return

        item = selected_items[0]
        note_title = self.notes_tree.item(item, "values")[0]

        decrypt_file("secure_notes.json", self.encryption_key)
        with open("secure_notes.json", "r") as file:
            notes = json.load(file)
        encrypt_file("secure_notes.json", self.encryption_key)

        selected_note = next((note for note in notes if note["title"] == note_title), None)
        if selected_note:
            self.title_entry.config(state="normal")
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, note_title)
            self.title_entry.config(state="disabled")

            decrypted_content = decrypt_data(selected_note['content'].encode(), self.encryption_key)
            self.note_content_text.config(state=tk.NORMAL)
            self.note_content_text.delete('1.0', tk.END)
            self.note_content_text.insert(tk.END, decrypted_content)
            self.note_content_text.config(state=tk.DISABLED)

    def search_notes(self, event=None):
        search_term = self.notes_search_entry.get().lower()
        self.notes_tree.delete(*self.notes_tree.get_children())
        if os.path.exists("secure_notes.json"):
            decrypt_file("secure_notes.json", self.encryption_key)
            with open("secure_notes.json", "r") as file:
                notes = json.load(file)
            encrypt_file("secure_notes.json", self.encryption_key)
            for note in notes:
                if search_term in note["title"].lower():
                    self.notes_tree.insert("", "end", values=(note["title"], note["date_added"]))

    def add_note_screen(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Add Secure Note'), font=("Helvetica", 20, "bold")).pack(pady=20)

        ttk.Label(frame, text=self.translate('Title')).pack(pady=5)
        self.note_title_entry = ttk.Entry(frame, width=100)
        self.note_title_entry.pack(pady=5)

        ttk.Label(frame, text=self.translate('Content')).pack(pady=5)
        self.note_content_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=200, height=25)
        self.note_content_text.pack(pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.translate("Save"), command=self.save_note, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text=self.translate("Back"), command=self.secure_notes_content, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()

    def save_note(self):
        title = self.note_title_entry.get()
        content = self.note_content_text.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showwarning(self.translate("Warning"), self.translate("Both title and content are required"))
            return

        encrypted_content = encrypt_data(content, self.encryption_key)
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_note = {
            "title": title,
            "content": encrypted_content.decode(),
            "date_added": date_added
        }

        notes = []
        if os.path.exists("secure_notes.json"):
            decrypt_file("secure_notes.json", self.encryption_key)
            with open("secure_notes.json", "r") as file:
                notes = json.load(file)
            encrypt_file("secure_notes.json", self.encryption_key)

        notes.append(new_note)

        with open("secure_notes.json", "w") as file:
            json.dump(notes, file, indent=2)
        encrypt_file("secure_notes.json", self.encryption_key)

        messagebox.showinfo(self.translate("Info"), self.translate("Note saved"))
        self.update_content('secure_notes')  # Use update_content instead of directly calling secure_notes_content


    def load_notes(self):
        self.notes_tree.delete(*self.notes_tree.get_children())
        if os.path.exists("secure_notes.json"):
            if os.path.getsize("secure_notes.json") > 0:  # Checks if the file is not empty
                try:
                    decrypt_file("secure_notes.json", self.encryption_key)
                    with open("secure_notes.json", "r") as file:
                        notes = json.load(file)
                    encrypt_file("secure_notes.json", self.encryption_key)
                    for note in notes:
                        self.notes_tree.insert("", "end", values=(note["title"], note["date_added"]))
                except (cryptography.fernet.InvalidToken, json.JSONDecodeError) as e:
                    print(f"Error decrypting or loading notes: {e}")
                    messagebox.showerror("Error", "Failed to load secure notes. The file may be corrupted.")
            else:
                print("secure_notes.json is empty.")
        else:
            print("secure_notes.json does not exist.")

    def view_note_content(self, event):
        selected_item = self.notes_tree.selection()
        if not selected_item:
            return

        item = self.notes_tree.item(selected_item)
        title = item['values'][0]

        decrypt_file("secure_notes.json", self.encryption_key)
        with open("secure_notes.json", "r") as file:
            notes = json.load(file)
        encrypt_file("secure_notes.json", self.encryption_key)

        note = next((n for n in notes if n['title'] == title), None)
        if note:
            decrypted_content = decrypt_data(note['content'].encode(), self.encryption_key)
            self.show_note_content(title, decrypted_content)

    def show_note_content(self, title, content):
        content_window = tk.Toplevel(self.root)
        content_window.title(title)
        content_window.geometry("600x400")
        self.center_window(600, 400, window=content_window)

        frame = ttk.Frame(content_window, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=title, font=("Helvetica", 16, "bold")).pack(pady=10)

        note_content = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=15)
        note_content.insert(tk.END, content)
        note_content.config(state=tk.DISABLED)
        note_content.pack(expand=True, fill="both")

        ttk.Button(frame, text=self.translate("Close"), command=content_window.destroy).pack(pady=10)

    def delete_selected_note(self):
        selected_item = self.notes_tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a note to delete"))
            return

        if messagebox.askyesno(self.translate("Delete Note"), self.translate("Are you sure you want to delete this note?")):
            item = self.notes_tree.item(selected_item)
            title_to_delete = str(item['values'][0])  # Convert to string to ensure consistent comparison

            decrypt_file("secure_notes.json", self.encryption_key)
            with open("secure_notes.json", "r") as file:
                notes = json.load(file)

            # Use string comparison for all titles
            notes = [note for note in notes if str(note['title']) != title_to_delete]

            with open("secure_notes.json", "w") as file:
                json.dump(notes, file, indent=2)
            encrypt_file("secure_notes.json", self.encryption_key)

            self.notes_tree.delete(selected_item)
            
            self.note_content_text.config(state=tk.NORMAL)
            self.note_content_text.delete('1.0', tk.END)
            self.note_content_text.config(state=tk.DISABLED)
            
            messagebox.showinfo(self.translate("Info"), self.translate("Note deleted"))

            self.load_notes()

    def settings_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Settings'), font=("Helvetica", 24, "bold")).pack(pady=20)

        button_style = "large.TButton"
        self.style.configure(button_style, font=("Helvetica", 14))

        button_width = 25  # Increased width for better appearance

        # Create a centered frame for buttons
        centered_frame = ttk.Frame(frame)
        centered_frame.pack(expand=True)

        # Password Generator button
        ttk.Button(centered_frame, text=self.translate('Password Generator'), 
                command=lambda: self.update_content('password_generator'), 
                style=button_style, 
                bootstyle=PRIMARY,
                width=button_width).pack(pady=10)

        # Auto Logout button
        ttk.Button(centered_frame, text=self.translate('Auto Logout'), 
                command=lambda: self.update_content('auto_logout'), 
                style=button_style, 
                bootstyle=INFO,
                width=button_width).pack(pady=10)

        # Username Generator button
        ttk.Button(centered_frame, text=self.translate('Username Generator'), 
                command=lambda: self.update_content('username_generator_settings'), 
                style=button_style, 
                bootstyle=WARNING,
                width=button_width).pack(pady=10)

        # Categories button
        ttk.Button(centered_frame, text=self.translate('Categories'), 
                command=lambda: self.update_content('categories'), 
                style=button_style, 
                bootstyle=SUCCESS,
                width=button_width).pack(pady=10)
        
        ttk.Button(centered_frame, text=self.translate('Face Recognition'), 
                command=self.face_recognition_settings, 
                style=button_style, 
                bootstyle=SECONDARY,
                width=button_width).pack(pady=10)
        
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        theme_switch = ttk.Button(
            bottom_frame,
            text=self.translate('Switch Theme'),
            command=self.toggle_theme,
            style='Outline.TButton'
        )
        theme_switch.pack(side=tk.LEFT)

        language_var = tk.StringVar(value=self.language)
        language_menu = ttk.Combobox(
            bottom_frame, 
            textvariable=language_var, 
            values=['English', 'Lithuanian'], 
            state='readonly'
        )
        language_menu.set(self.language)
        language_menu.pack(side=tk.RIGHT)
        language_menu.bind('<<ComboboxSelected>>', lambda event: self.change_language(language_var.get()))

        self.auto_logout.reset()
        self.auto_logout.start()

    def back_command(self):
        print(f"Current navigation history: {self.navigation_history}")
        if len(self.navigation_history) > 1:
            current_screen = self.navigation_history.pop()
            previous_screen = self.navigation_history[-1]
            print(f"Navigating back from {current_screen} to {previous_screen}")
            if previous_screen != current_screen:  # Prevents re-entering the same screen
                if previous_screen == 'add_password':
                    self.add_password_screen()
                elif previous_screen == 'edit_password':
                    self.edit_password_screen(self.selected_item_values)
                elif previous_screen == 'settings':
                    self.settings_screen()
                elif previous_screen == 'password_generator':
                    self.password_generator_screen()
                elif previous_screen == 'auto_logout':
                    self.auto_logout_screen()
                elif previous_screen == 'username_generator_settings':
                    self.username_generator_settings_screen()
                elif previous_screen == 'categories':
                    self.categories_screen()
                elif previous_screen == 'password_manager':
                    self.password_manager_screen()
                else:
                    print(f"Unknown previous screen: {previous_screen}")
                    self.password_manager_screen()
            else:
                print(f"Prevented re-entering the same screen: {current_screen}")
        else:
            print("Navigation history is empty or has only one item")
            self.password_manager_screen()
    
    def face_recognition_settings(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Face Recognition Settings'), font=("Helvetica", 24, "bold")).pack(pady=20)

        def toggle_face_recognition():
            if self.face_recognition_var.get():
                if not self.face_recognition_enabled:
                    warning_message = self.translate("Enabling face recognition will use your webcam or camera to capture a photo of your face for authentication. Do you want to proceed?")
                    if messagebox.askyesno(self.translate("Face Recognition Warning"), warning_message):
                        self.capture_face_image()
                    else:
                        self.face_recognition_var.set(False)  # Reset checkbox if user cancels
                else:
                    messagebox.showinfo(self.translate("Face Recognition"), self.translate("Face Recognition is already enabled"))
            else:
                self.face_recognition_auth.disable_face_recognition()
                self.face_recognition_enabled = False
                messagebox.showinfo(self.translate("Face Recognition"), self.translate("Face Recognition disabled"))
            self.update_face_image_display()

        self.face_recognition_var = tk.BooleanVar(value=self.face_recognition_enabled)
        ttk.Checkbutton(frame, text=self.translate('Enable Face Recognition'), 
                        variable=self.face_recognition_var, 
                        command=toggle_face_recognition).pack(pady=10)

        self.face_image_label = ttk.Label(frame)
        self.face_image_label.pack(pady=10)

        ttk.Button(frame, text=self.translate('Upload Face Image'), 
                command=self.upload_face_image, 
                state='normal' if self.face_recognition_enabled else 'disabled').pack(pady=10)
        
        ttk.Button(frame, text=self.translate('Capture Face Image'), 
                command=self.capture_face_image, 
                state='normal' if self.face_recognition_enabled else 'disabled').pack(pady=10)

        # Add an information label
        info_text = self.translate("Face recognition uses your camera to capture an image for authentication. Your privacy and data security are our priority.")
        ttk.Label(frame, text=info_text, wraplength=400, justify="center").pack(pady=20)

        self.update_face_image_display()

    def update_face_image_display(self):
        image_data = self.face_recognition_auth.get_original_face_image()
        if image_data and self.face_recognition_enabled:
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            self.face_image_label.config(image=photo)
            self.face_image_label.image = photo
        else:
            self.face_image_label.config(image='')
        
        # Update button states
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and child['text'] in [self.translate('Upload Face Image'), self.translate('Capture Face Image')]:
                        child['state'] = 'normal' if self.face_recognition_enabled else 'disabled'

    def upload_face_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            with open(file_path, "rb") as f:
                image_data = f.read()
            if self.face_recognition_auth.enable_face_recognition(image_data):
                messagebox.showinfo(self.translate("Success"), self.translate("Face image uploaded successfully."))
                self.update_face_image_display()
            else:
                messagebox.showerror(self.translate("Error"), self.translate("No face detected in the image. Please try again."))

    def capture_face_image(self):
        try:
            image_data = self.face_recognition_auth.capture_image_from_webcam()
            if image_data:
                if self.face_recognition_auth.enable_face_recognition(image_data):
                    self.face_recognition_enabled = True
                    messagebox.showinfo(self.translate("Face Recognition"), self.translate("Face Recognition enabled"))
                else:
                    messagebox.showerror(self.translate("Error"), self.translate("Failed to detect a face in the image. Please try again."))
            else:
                self.handle_camera_error()
        except Exception as e:
            print(f"Camera error: {str(e)}")
            self.handle_camera_error()
        finally:
            self.update_face_image_display()
    
    def handle_camera_error(self):
        error_message = self.translate("Error: Camera not found or cannot be accessed. Please check your camera connection and try again.")
        messagebox.showerror(self.translate("Camera Error"), error_message)
        self.face_recognition_var.set(False)
        self.face_recognition_enabled = False

    def update_face_image_display(self):
        image_data = self.face_recognition_auth.get_original_face_image()
        if image_data and self.face_recognition_enabled:
            try:
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(image)
                self.face_image_label.config(image=photo)
                self.face_image_label.image = photo
            except Exception as e:
                print(f"Error displaying face image: {str(e)}")
                self.face_image_label.config(image='')
        else:
            self.face_image_label.config(image='')
        
        # Update button states
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and child['text'] in [self.translate('Upload Face Image'), self.translate('Capture Face Image')]:
                        child['state'] = 'normal' if self.face_recognition_enabled else 'disabled'

    def password_generator_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Password Generator'), font=("Helvetica", 24, "bold")).pack(pady=(0, 20))

        # Passwords display
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(frame, textvariable=self.password_var, font=("Helvetica", 14), width=30)
        password_entry.pack(pady=(0, 10))

        generate_button = ttk.Button(frame, text=self.translate('Generate'), 
                                    command=self.generate_password_preview, 
                                    style="large.TButton", 
                                    bootstyle=SUCCESS,
                                    width=20)
        generate_button.pack(pady=(0, 20))

        center_container = ttk.Frame(frame)
        center_container.pack(fill="x", expand=True, pady=(0, 20))

        ttk.Frame(center_container).pack(side="left", expand=True)

        options_frame = ttk.Frame(center_container)
        options_frame.pack(side="left")

        # Length slider
        slider_frame = ttk.Frame(options_frame)
        slider_frame.pack(side="left", padx=(0, 20))

        ttk.Label(slider_frame, text=self.translate('Length:')).pack()
        self.length_var = tk.IntVar(value=utils.PASSWORD_LENGTH)
        length_slider = ttk.Scale(slider_frame, from_=8, to=32, variable=self.length_var, 
                                orient="horizontal", length=200, command=self.update_length_label)
        length_slider.pack()
        self.length_label = ttk.Label(slider_frame, text=str(utils.PASSWORD_LENGTH))
        self.length_label.pack()

        # Checkboxes
        checkbox_frame = ttk.Frame(options_frame)
        checkbox_frame.pack(side="left")

        self.uppercase_var = tk.BooleanVar(value=utils.USE_UPPERCASE)
        self.lowercase_var = tk.BooleanVar(value=utils.USE_LOWERCASE)
        self.digits_var = tk.BooleanVar(value=utils.USE_DIGITS)
        self.symbols_var = tk.BooleanVar(value=utils.USE_SYMBOLS)

        ttk.Checkbutton(checkbox_frame, text=self.translate('Uppercase'), variable=self.uppercase_var, command=self.check_for_changes).pack(anchor="w")
        ttk.Checkbutton(checkbox_frame, text=self.translate('Lowercase'), variable=self.lowercase_var, command=self.check_for_changes).pack(anchor="w")
        ttk.Checkbutton(checkbox_frame, text=self.translate('Numbers'), variable=self.digits_var, command=self.check_for_changes).pack(anchor="w")
        ttk.Checkbutton(checkbox_frame, text=self.translate('Symbols'), variable=self.symbols_var, command=self.check_for_changes).pack(anchor="w")

        ttk.Frame(center_container).pack(side="left", expand=True)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))

        button_width = 15

        ttk.Button(button_frame, text=self.translate('Restore Defaults'), 
                command=self.restore_default_password_settings, 
                style="large.TButton", 
                bootstyle=INFO,
                width=button_width).pack(side="left", padx=5, expand=True)

        self.save_button = ttk.Button(button_frame, text=self.translate('Save'), 
                command=self.save_password_settings, 
                style="large.TButton", 
                bootstyle=PRIMARY,
                width=button_width)

        self.discard_button = ttk.Button(button_frame, text=self.translate('Discard'), 
                command=self.discard_password_settings, 
                style="large.TButton", 
                bootstyle=SECONDARY,
                width=button_width)

        self.check_for_changes()
        self.auto_logout.reset()
        self.auto_logout.start()

    def update_length_label(self, value=None):
        if value is None:
            value = self.length_var.get()
        self.length_label.config(text=str(int(float(value))))
        self.check_for_changes()

    def check_for_changes(self):
        changes_made = (
            int(self.length_var.get()) != utils.PASSWORD_LENGTH or
            self.uppercase_var.get() != utils.USE_UPPERCASE or
            self.lowercase_var.get() != utils.USE_LOWERCASE or
            self.digits_var.get() != utils.USE_DIGITS or
            self.symbols_var.get() != utils.USE_SYMBOLS
        )

        if changes_made:
            self.save_button.pack(side="left", padx=5, expand=True)
            self.discard_button.pack(side="left", padx=5, expand=True)
        else:
            self.save_button.pack_forget()
            self.discard_button.pack_forget()

    def generate_password_preview(self):
        password = utils.generate_password(
            length=int(self.length_var.get()),
            use_uppercase=self.uppercase_var.get(),
            use_lowercase=self.lowercase_var.get(),
            use_digits=self.digits_var.get(),
            use_symbols=self.symbols_var.get()
        )
        self.password_var.set(password)

    def save_password_settings(self):
        utils.PASSWORD_LENGTH = int(self.length_var.get())
        utils.USE_UPPERCASE = self.uppercase_var.get()
        utils.USE_LOWERCASE = self.lowercase_var.get()
        utils.USE_DIGITS = self.digits_var.get()
        utils.USE_SYMBOLS = self.symbols_var.get()
        utils.save_settings()  # Saves settings to file
        messagebox.showinfo(self.translate("Success"), self.translate("Password settings saved successfully"))
        self.check_for_changes()
    
    def discard_password_settings(self):
        self.length_var.set(utils.PASSWORD_LENGTH)
        self.uppercase_var.set(utils.USE_UPPERCASE)
        self.lowercase_var.set(utils.USE_LOWERCASE)
        self.digits_var.set(utils.USE_DIGITS)
        self.symbols_var.set(utils.USE_SYMBOLS)
        self.update_length_label()  # Updates the length label
        self.check_for_changes()

    def check_for_changes(self):
        changes_made = (
            int(self.length_var.get()) != utils.PASSWORD_LENGTH or
            self.uppercase_var.get() != utils.USE_UPPERCASE or
            self.lowercase_var.get() != utils.USE_LOWERCASE or
            self.digits_var.get() != utils.USE_DIGITS or
            self.symbols_var.get() != utils.USE_SYMBOLS
        )

        if changes_made:
            self.save_button.pack(side="left", padx=5, expand=True)
            self.discard_button.pack(side="left", padx=5, expand=True)
        else:
            self.save_button.pack_forget()
            self.discard_button.pack_forget()

    def restore_default_password_settings(self):
        utils.PASSWORD_LENGTH = 12
        utils.USE_UPPERCASE = True
        utils.USE_LOWERCASE = True
        utils.USE_DIGITS = True
        utils.USE_SYMBOLS = True
        utils.save_settings()  # Saves default settings to file
        self.discard_password_settings()

    def auto_logout_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Auto Logout Settings'), font=("Helvetica", 24, "bold")).pack(pady=20)

        ttk.Label(frame, text=self.translate('Auto Logout Time (seconds):')).pack(pady=5)
        self.auto_logout_entry = ttk.Entry(frame)
        self.auto_logout_entry.insert(0, str(self.auto_logout_time))
        self.auto_logout_entry.pack(pady=5)
        self.auto_logout_entry.bind("<KeyRelease>", self.check_auto_logout_changes)

        button_frame1 = ttk.Frame(frame)
        button_frame1.pack(fill="x", pady=10)

        ttk.Button(button_frame1, text=self.translate('Restore Default'), 
                command=self.restore_default_auto_logout, 
                style="large.TButton", 
                bootstyle=INFO,
                width=20).pack(side="left", padx=5, expand=True)

        self.button_frame2 = ttk.Frame(frame)
        self.button_frame2.pack(fill="x", pady=10)

        self.save_button = ttk.Button(self.button_frame2, text=self.translate('Save'), 
                                    command=self.save_auto_logout_settings, 
                                    style="large.TButton", 
                                    bootstyle=SUCCESS,
                                    width=20)

        self.discard_button = ttk.Button(self.button_frame2, text=self.translate('Discard'), 
                                        command=self.discard_auto_logout_changes, 
                                        style="large.TButton", 
                                        bootstyle=SECONDARY,
                                        width=20)

        self.check_auto_logout_changes()
        self.auto_logout.reset()
        self.auto_logout.start()

    def check_auto_logout_changes(self, event=None):
        current_value = self.auto_logout_entry.get()
        try:
            current_value = int(current_value)
            changes_made = current_value != self.auto_logout_time
        except ValueError:
            changes_made = True

        if changes_made:
            self.save_button.pack(side="left", padx=5, expand=True)
            self.discard_button.pack(side="left", padx=5, expand=True)
        else:
            self.save_button.pack_forget()
            self.discard_button.pack_forget()

    def restore_default_auto_logout(self):
        default_timeout = 300  #300seconds = 5 minutes
        self.auto_logout_entry.delete(0, tk.END)
        self.auto_logout_entry.insert(0, str(default_timeout))
        self.check_auto_logout_changes()

    def discard_auto_logout_changes(self):
        self.auto_logout_entry.delete(0, tk.END)
        self.auto_logout_entry.insert(0, str(self.auto_logout_time))
        self.check_auto_logout_changes()

    def save_auto_logout_settings(self):
        try:
            new_time = int(self.auto_logout_entry.get())
            if new_time < 10:  # Minimum 10 seconds to prevent accidental lockouts
                raise ValueError(self.translate("Auto logout time must be at least 10 seconds."))
            self.auto_logout_time = new_time
            self.auto_logout.timeout = new_time
            
            settings = {'auto_logout_time': new_time}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
            
            messagebox.showinfo(self.translate("Success"), self.translate("Auto logout settings saved successfully."))
            self.check_auto_logout_changes()
        except ValueError as e:
            messagebox.showerror(self.translate("Error"), str(e))

    def username_generator_settings_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Username Generator Settings'), font=("Helvetica", 24, "bold")).pack(pady=20)

        notebook = ttk.Notebook(frame)
        notebook.pack(expand=True, fill="both")

        adjectives_frame = ttk.Frame(notebook)
        nouns_frame = ttk.Frame(notebook)

        notebook.add(adjectives_frame, text=self.translate('Adjectives'))
        notebook.add(nouns_frame, text=self.translate('Nouns'))

        self.setup_word_list_ui(adjectives_frame, 'adjectives')
        self.setup_word_list_ui(nouns_frame, 'nouns')

        self.auto_logout.reset()
        self.auto_logout.start()

    def setup_word_list_ui(self, parent_frame, word_type):
        frame = ttk.Frame(parent_frame)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        columns = ("Word",)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        tree.heading("Word", text=self.translate("Word"))
        tree.column("Word", width=200, anchor="center")
        tree.pack(side="left", expand=True, fill="both")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        # Loads words into the Treeview
        words = self.load_words(word_type)
        for word in words:
            tree.insert("", "end", values=(word,))

        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.translate("Add"), 
                command=lambda: self.add_word(tree, word_type)).pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Edit"), 
                command=lambda: self.edit_word(tree, word_type)).pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Delete"), 
                command=lambda: self.delete_word(tree, word_type)).pack(side="left", padx=5)

    def load_words(self, word_type):
        default_words = self.get_default_words(word_type)
        try:
            with open(f'{word_type}.json', 'r') as f:
                saved_words = json.load(f)
            # Combine default words with saved words, removing duplicates
            return list(dict.fromkeys(default_words + saved_words))
        except FileNotFoundError:
            return default_words

    def get_default_words(self, word_type):
        if word_type == 'adjectives':
            return ['happy', 'sunny', 'clever', 'brave', 'mighty', 'kind', 'swift', 'cool']
        elif word_type == 'nouns':
            return ['tiger', 'sun', 'moon', 'star', 'eagle', 'lion', 'wolf', 'bear']
        return []

    def save_words(self, word_type, words):
        with open(f'{word_type}.json', 'w') as f:
            json.dump(words, f)

    def add_word(self, tree, word_type):
        new_word = simpledialog.askstring(self.translate("Add Word"), self.translate(f"Enter new {word_type[:-1]}:"))
        if new_word:
            tree.insert("", "end", values=(new_word,))
            words = [tree.item(child)["values"][0] for child in tree.get_children()]
            self.save_words(word_type, words)

    def edit_word(self, tree, word_type):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning(
                self.translate("Warning"),
                self.translate("Please select a {0} to edit").format(self.translate(word_type[:-1]))
            )
            return
        
        current_word = tree.item(selected_item)['values'][0]
        new_word = simpledialog.askstring(
            self.translate("Edit Word"), 
            self.translate("Edit {0}:").format(self.translate(word_type[:-1])), 
            initialvalue=current_word
        )
        
        if new_word and new_word != current_word:
            tree.item(selected_item, values=(new_word,))
            words = [tree.item(child)["values"][0] for child in tree.get_children()]
            self.save_words(word_type, words)

    def delete_word(self, tree, word_type):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning(
                self.translate("Warning"), 
                self.translate("Please select a {0} to delete").format(self.translate(word_type[:-1]))
            )
            return
        
        if messagebox.askyesno(
            self.translate("Confirm Deletion"), 
            self.translate("Are you sure you want to delete this {0}?").format(self.translate(word_type[:-1]))
        ):
            tree.delete(selected_item)
            words = [tree.item(child)["values"][0] for child in tree.get_children()]
            self.save_words(word_type, words)

    def categories_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Categories'), font=("Helvetica", 24, "bold")).pack(pady=20)

        # Creates a treeview to display categories
        columns = ("Category",)
        self.categories_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.categories_tree.heading("Category", text=self.translate("Category"))
        self.categories_tree.column("Category", width=200, anchor="center")
        self.categories_tree.pack(pady=10, fill="both", expand=True)

        self.load_categories()

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.translate("Add Category"), command=self.add_category, style="primary.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Edit Category"), command=self.edit_category, style="info.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Delete Category"), command=self.delete_category, style="danger.TButton").pack(side="left", padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()

    def load_categories(self):
        self.categories_tree.delete(*self.categories_tree.get_children())
        categories = sorted(self.get_categories(), key=str.lower)
        print(f"Loading categories: {categories}")
        for category in categories:
            self.categories_tree.insert("", "end", values=(category,))

    def get_categories(self):
        if os.path.exists("categories.json"):
            with open("categories.json", "r") as file:
                categories = json.load(file)
                print(f"Categories loaded from file: {categories}")
                return categories
        default_categories = ["Work", "Personal", "Finance", "School", "Other"]
        print(f"Using default categories: {default_categories}")
        return default_categories

    def save_categories(self, categories):
        print(f"Saving categories: {categories}")
        with open("categories.json", "w") as file:
            json.dump(categories, file, indent=2)
        
        # Verifies the save
        with open("categories.json", "r") as file:
            saved_categories = json.load(file)
        print(f"Categories saved and verified: {saved_categories}")

    def add_category(self):
        new_category = simpledialog.askstring(self.translate("Add Category"), self.translate("Enter new category name:"))
        if new_category:
            categories = self.get_categories()
            if not any(str(cat).lower() == str(new_category).lower() for cat in categories):
                categories.append(new_category)
                self.save_categories(categories)
                self.load_categories()
                print(f"New category added: {new_category}")
            else:
                print(f"Category '{new_category}' already exists (case-insensitive)")

    def edit_category(self):
        selected_item = self.categories_tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a category to edit"))
            return
        
        old_category = self.categories_tree.item(selected_item)['values'][0]
        new_category = simpledialog.askstring(self.translate("Edit Category"), self.translate("Enter new category name:"), initialvalue=old_category)
        
        if new_category and new_category != old_category:
            categories = self.get_categories()
            if new_category not in categories:
                categories = [new_category if cat == old_category else cat for cat in categories]
                self.save_categories(categories)
                self.load_categories()
                self.update_password_categories(old_category, new_category)
                messagebox.showinfo(self.translate("Success"), self.translate("Category updated successfully"))
            else:
                messagebox.showwarning(self.translate("Warning"), self.translate("Category already exists"))

    def delete_category(self):
        selected_item = self.categories_tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a category to delete"))
            return
        
        category_to_delete = self.categories_tree.item(selected_item)['values'][0]
        print(f"Attempting to delete category: {category_to_delete}")
        
        if messagebox.askyesno(self.translate("Confirm Deletion"), self.translate("Are you sure you want to delete the category '{0}'?").format(category_to_delete)):
            categories = self.get_categories()
            print(f"Current categories before deletion: {categories}")
            
            category_index = next((i for i, cat in enumerate(categories) if str(cat).lower() == str(category_to_delete).lower()), -1)
            if category_index != -1:
                del categories[category_index]
                print(f"Categories after removal: {categories}")
                self.save_categories(categories)
                self.update_password_categories(category_to_delete, "Other")
                messagebox.showinfo(self.translate("Success"), self.translate("Category deleted successfully"))
            else:
                print(f"Category '{category_to_delete}' not found in the list.")
            
            self.load_categories()

    def update_password_categories(self, old_category, new_category):
        try:
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            
            updated = False
            for password in passwords:
                if password.get("category") == old_category:
                    password["category"] = new_category
                    updated = True
            
            if updated:
                with open("passwords.json", "w") as file:
                    json.dump(passwords, file, indent=2)
                encrypt_file("passwords.json", self.encryption_key)
        except InvalidToken:
            print("Unable to decrypt passwords file. The encryption key may be incorrect.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            # Ensures the file is re-encrypted even if an error occurred
            try:
                encrypt_file("passwords.json", self.encryption_key)
            except Exception:
                pass
    
    def clean_categories(self):
        categories = self.get_categories()
        cleaned_categories = []
        seen = set()
        for category in categories:
            if str(category).lower() not in seen:
                cleaned_categories.append(category)
                seen.add(str(category).lower())
        if len(cleaned_categories) != len(categories):
            print(f"Cleaned categories: {cleaned_categories}")
            self.save_categories(cleaned_categories)
        return cleaned_categories
    

    def add_password_content(self):
    # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Add New Password'), font=("Helvetica", 20, "bold")).pack(pady=20)

        input_style = "TEntry"
        self.style.configure(input_style, padding=10)

        ttk.Label(frame, text=self.translate('Name/Website')).pack(pady=5)
        self.site_entry = ttk.Entry(frame, style=input_style)
        self.site_entry.pack(pady=5, fill="x")

        ttk.Label(frame, text=self.translate("Username/Email")).pack(pady=5)
        username_frame = ttk.Frame(frame)
        username_frame.pack(pady=5, fill="x")
        self.username_entry = ttk.Entry(username_frame, style=input_style)
        self.username_entry.pack(side="left", fill="x", expand=True)

        ttk.Label(frame, text=self.translate("Password")).pack(pady=5)
        password_frame = ttk.Frame(frame)
        password_frame.pack(pady=5, fill="x")
        self.password_entry = ttk.Entry(password_frame, show="*", style=input_style)
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.show_password_var = tk.BooleanVar()
        eye_button = ttk.Checkbutton(password_frame, text="👁", command=self.toggle_password_visibility, 
                                    variable=self.show_password_var, style='info.Outline.TButton')
        eye_button.pack(side="right", padx=5)

        ttk.Label(frame, text=self.translate("Category")).pack(pady=5)
        categories = self.get_categories()
        category_dropdown = ttk.Combobox(frame, textvariable=self.category_var, values=categories, state="readonly")
        category_dropdown.pack(pady=5, fill="x")
        category_dropdown.set("Personal")

        generate_button_frame = ttk.Frame(frame)
        generate_button_frame.pack(pady=10)

        generate_username_button = ttk.Button(generate_button_frame, text=self.translate("Generate Username"), 
                                    command=self.generate_and_insert_username, bootstyle=(INFO, OUTLINE))
        generate_username_button.pack(side="left", padx=(0, 5))

        generate_password_button = ttk.Button(generate_button_frame, text=self.translate("Generate Password"), 
                                    command=self.generate_and_insert_password, bootstyle=(INFO, OUTLINE))
        generate_password_button.pack(side="left", padx=(5, 0))

        strength_suggestions_frame = ttk.Frame(frame, height=120) 
        strength_suggestions_frame.pack(pady=5, fill="x")
        strength_suggestions_frame.pack_propagate(False)  

        self.password_strength_frame = ttk.Frame(strength_suggestions_frame)
        self.password_strength_frame.pack(pady=5, fill="x")

        self.password_strength_label = ttk.Label(self.password_strength_frame, text=self.translate("Password Strength: "))
        self.password_strength_label.pack(side="left")

        self.password_strength_meter = ttk.Progressbar(self.password_strength_frame, length=200, mode='determinate')
        self.password_strength_meter.pack(side="left", padx=5)

        self.password_suggestions_label = ttk.Label(strength_suggestions_frame, text="", wraplength=700)
        self.password_suggestions_label.pack(pady=5, fill="x")

        self.password_entry.bind("<KeyRelease>", self.update_password_strength)

        self.format_url_var = tk.BooleanVar()
        self.format_url_checkbox = ttk.Checkbutton(frame, text=self.translate("Automatically add 'https://' and 'www.'"), 
                                                variable=self.format_url_var)
        self.format_url_checkbox.pack(pady=5)

        ttk.Button(frame, text=self.translate("Save"), command=self.save_password, bootstyle=SUCCESS).pack(pady=5)

        self.auto_logout.reset()
        self.auto_logout.start()

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def generate_and_insert_password(self):
        password = generate_password()
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self.update_password_strength()

    def save_password(self):
        site = self.site_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        category = self.category_var.get()

        if self.format_url_var.get():
            site = format_url(site)

        # Checks if an identical entry already exists
        if self.is_duplicate_entry(site, username, password):
            messagebox.showwarning(self.translate("Warning"), 
                                self.translate("An identical password entry already exists. No changes were made."))
            return

        encrypted_password = encrypt_data(password, self.encryption_key)
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_entry = {
            "site": site,
            "username": username,
            "current_password": encrypted_password.decode(),
            "category": category,
            "history": [{
                "password": encrypted_password.decode(),
                "date": date_added,
                "site": site,
                "username": username,
                "category": category
            }]
        }

        passwords = []
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)

        passwords.append(new_entry)

        with open("passwords.json", "w") as file:
            json.dump(passwords, file, indent=2)
        encrypt_file("passwords.json", self.encryption_key)

        messagebox.showinfo(self.translate("Info"), self.translate("Password saved"))
        self.check_expired_passwords()
        self.password_manager_screen()
        

    def update_password_strength(self, event=None):
        password = self.password_entry.get()
        strength, color, suggestions = check_password_strength(password)
        translated_strength = self.translate(strength)
        self.password_strength_label.config(text=f"{self.translate('Password Strength:')} {translated_strength}")
        
        if color == "red":
            value = 25
        elif color == "orange":
            value = 50
        elif color == "yellow":
            value = 75
        else:  # green
            value = 100
        
        self.password_strength_meter['value'] = value
        self.password_strength_meter['style'] = f"{color}.Horizontal.TProgressbar"

        self.update_password_suggestions(suggestions)

    def update_password_suggestions(self, suggestions):
        if hasattr(self, 'suggestion_labels'):
            for label in self.suggestion_labels:
                label.destroy()
        
        self.suggestion_labels = []
        for suggestion in suggestions:
            label = ttk.Label(self.password_strength_frame, text=f"• {self.translate(suggestion)}", font=("Helvetica", 10), foreground="gray")
            label.pack(anchor="w")
            self.suggestion_labels.append(label)

    def view_passwords_content(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=self.translate("Stored Passwords"), font=("Helvetica", 24, "bold")).pack(pady=20)

        search_frame = ttk.Frame(frame)
        search_frame.pack(pady=10, fill="x")

        ttk.Label(search_frame, text=self.translate("Search:"), font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.search_entry = ttk.Entry(search_frame, style="TEntry", font=("Helvetica", 14))
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.search_passwords)

        filter_sort_frame = ttk.Frame(frame)
        filter_sort_frame.pack(pady=10, fill="x")

        filter_frame = ttk.Frame(filter_sort_frame)
        filter_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(filter_frame, text=self.translate("Filter by:")).pack(side="left", padx=(0, 10))
        self.filter_column_var = tk.StringVar()
        columns = ["All", "Site", "Username", "Password", "Date Added", "Date Edited", "Categories"]
        self.filter_column_dropdown = ttk.Combobox(filter_frame, textvariable=self.filter_column_var, values=columns, state="readonly")
        self.filter_column_dropdown.pack(side="left", fill="x", expand=True)
        self.filter_column_dropdown.set("All")
        self.filter_column_dropdown.bind("<<ComboboxSelected>>", self.update_sort_options)

        sort_frame = ttk.Frame(filter_sort_frame)
        sort_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ttk.Label(sort_frame, text=self.translate("Sort by:")).pack(side="left", padx=(20, 10))
        self.sort_order_var = tk.StringVar(value="A-Z")
        self.sort_order_dropdown = ttk.Combobox(sort_frame, textvariable=self.sort_order_var, values=["A-Z", "Z-A"], state="readonly")
        self.sort_order_dropdown.pack(side="left", fill="x", expand=True)

        ttk.Button(filter_sort_frame, text=self.translate("Apply"), command=self.apply_filter_and_sort).pack(side="left", padx=(10, 0))

        columns = ("Checkbox", "Site", "Username", "Password", "Date Added", "Date Edited", "Category", "Reveal")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", style="Custom.Treeview")

        self.style.configure("Custom.Treeview", font=('Helvetica', 12))
        self.style.configure("Custom.Treeview.Heading", font=('Helvetica', 14, 'bold'))

        for col in columns:
            translated_col = self.translate(col)
            self.tree.heading(col, text=translated_col)
            if col == "Checkbox":
                self.tree.column(col, width=30, anchor="center", stretch=False)
            elif col == "Site":
                self.tree.column(col, width=200, anchor="w", stretch=True)
            elif col in ("Username", "Password", "Date Added", "Date Edited", "Category"):
                self.tree.column(col, width=150, anchor="center", stretch=True)

        self.tree.heading("Checkbox", text="")

        self.tree.pack(fill="both", expand=True)

        self.load_passwords()
        

        self.tree.bind("<Button-1>", self.toggle_checkbox)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Motion>", self.on_tree_motion)
        self.tree.bind("<Button-1>", self.handle_tree_click)

        self.tree.column("Reveal", width=50, anchor="center", stretch=False)
        self.tree.heading("Reveal", text="")

        self.context_menu = Menu(self.content_frame, tearoff=0)
        for i, column in enumerate(self.tree['columns']):
            translated_col = self.translate(column)
            self.context_menu.add_command(label=f"{self.translate('Copy')} {translated_col}", 
                                        command=lambda i=i: self.copy_to_clipboard(i))
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        button_style = "large.TButton"
        self.style.configure(button_style, font=("Helvetica", 14))

        self.check_expired_passwords()

        def edit_selected_password():
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning(self.translate("Warning"), self.translate("Please select a password to edit"))
                return
            
            item = self.tree.item(selected_items[0])
            values = item['values']
            stored_values = values[1:-1]
            
            # If the password is hidden (asterisks), get the actual password
            if stored_values[2] == "*" * 8:
                encrypted_password = item['tags'][0]
                decrypted_password = decrypt_data(encrypted_password.encode(), self.encryption_key)
                stored_values = list(stored_values)
                stored_values[2] = decrypted_password
                stored_values = tuple(stored_values)

            self.update_content('edit_password', stored_values)

        ttk.Button(button_frame, text=self.translate("Edit Selected"), 
            command=edit_selected_password, 
            style="primary.TButton", 
            width=20).pack(side="left", padx=5)

        ttk.Button(button_frame, text=self.translate("Delete Selected"), 
            command=self.delete_selected_passwords, 
            style="danger.TButton", 
            width=20).pack(side="left", padx=5)

        ttk.Button(button_frame, text=self.translate("View History"), 
            command=self.view_password_history, 
            style="primary.TButton", 
            width=20).pack(side="left", padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()
    

    def load_passwords(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)
            for entry in passwords:
                site = str(entry["site"])
                username = str(entry["username"])
                encrypted_password = entry["current_password"]
                date_added = entry["history"][0]["date"]
                date_edited = entry["history"][-1]["date"] if len(entry["history"]) > 1 else ""
                category = entry.get("category", "")
                hidden_password = "*" * 8  # Hide password with asterisks
                item = self.tree.insert("", "end", values=("☐", site, username, hidden_password, date_added, date_edited, category, "👁"))
                # Store the actual encrypted password in the tree item
                self.tree.item(item, tags=(encrypted_password,))

        self.tree.column("Checkbox", width=30, anchor="center", stretch=False)
        self.tree.column("Site", width=200, anchor="w", stretch=True)
        for col in ("Username", "Password", "Date Added", "Date Edited", "Category"):
            self.tree.column(col, width=150, anchor="center", stretch=True)
        self.tree.column("Reveal", width=50, anchor="center", stretch=False)

        self.check_expired_passwords()

    def check_expired_passwords(self):
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)

            current_time = datetime.now()
            expired_passwords = []

            for entry in passwords:
                site = entry["site"]
                username = entry["username"]
                date_added = datetime.strptime(entry["history"][0]["date"], "%Y-%m-%d %H:%M:%S")
                date_edited = datetime.strptime(entry["history"][-1]["date"], "%Y-%m-%d %H:%M:%S") if len(entry["history"]) > 1 else date_added

                
                if current_time - date_edited > timedelta(days=30):
                    expired_passwords.append(f"{site} - {username}")

            
            if expired_passwords:
                expired_set = set(expired_passwords) - self.expired_passwords
                if expired_set:
                    message = self.translate("The following passwords have expired:") + "\n\n"
                    message += "\n".join(expired_set)
                    messagebox.showwarning(self.translate("Expired Passwords"), message)
                    self.expired_passwords.update(expired_set)



    def update_sort_options(self, event=None):
        selected_column = self.filter_column_var.get()
        if selected_column == "Categories":
            categories = self.get_categories()
            self.sort_order_dropdown['values'] = ["All"] + categories
            self.sort_order_var.set("All")
        else:
            self.sort_order_dropdown['values'] = ["A-Z", "Z-A"]
            self.sort_order_var.set("A-Z")

    def apply_filter_and_sort(self):
        filter_column = self.filter_column_var.get()
        sort_order = self.sort_order_var.get()

        self.load_passwords()

        if filter_column != "All":
            filtered_items = []
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                if filter_column == "Categories":
                    if sort_order == "All" or values[6] == sort_order:
                        filtered_items.append(item)
                elif filter_column in ["Site", "Username", "Password", "Date Added", "Date Edited"]:
                    column_index = self.tree["columns"].index(filter_column)
                    if values[column_index]:
                        filtered_items.append(item)
            
            for item in self.tree.get_children():
                if item not in filtered_items:
                    self.tree.detach(item)

        # Determines the column to sort by
        if filter_column == "Categories":
            sort_column = "Category"
        elif filter_column == "All":
            sort_column = "Site"
        else:
            sort_column = filter_column

        reverse = sort_order == "Z-A"
        
        if filter_column == "Categories" and sort_order != "All":
            l = [(1 if self.tree.set(k, "Category") == sort_order else 0, self.tree.set(k, "Site").lower(), k) for k in self.tree.get_children('')]
        else:
            l = [(self.tree.set(k, sort_column).lower(), k) for k in self.tree.get_children('')]
        
        l.sort(reverse=reverse)

        for index, item in enumerate(l):
            self.tree.move(item[-1], '', index)

    def filter_passwords(self, event=None):
        selected_category = self.category_filter_var.get()
        self.tree.delete(*self.tree.get_children())
            
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)
                
            for entry in passwords:
                if selected_category == "All" or entry.get("category", "") == selected_category:
                    site = str(entry["site"])
                    username = str(entry["username"])
                    encrypted_password = entry["current_password"]
                    date_added = entry["history"][0]["date"]
                    date_edited = entry["history"][-1]["date"] if len(entry["history"]) > 1 else ""
                    category = entry.get("category", "")
                    decrypted_password = decrypt_data(encrypted_password.encode(), self.encryption_key)
                    self.tree.insert("", "end", values=("☐", site, username, decrypted_password, date_added, date_edited, category))

    def sort_passwords(self):
        column = self.sort_column_var.get()
        reverse = self.sort_order_var.get() == "Z-A"
        column_index = self.tree["columns"].index(column)

        items = [(self.tree.set(k, column), k) for k in self.tree.get_children('')]

        items.sort(reverse=reverse, key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0])

        # Rearranges items in sorted positions
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

    def search_passwords(self, event=None):
        search_term = self.search_entry.get().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)
            for entry in passwords:
                site = str(entry["site"])
                username = str(entry["username"])
                encrypted_password = entry["current_password"]
                date_added = entry["history"][0]["date"]
                date_edited = entry["history"][-1]["date"] if len(entry["history"]) > 1 else ""
                category = entry.get("category", "")
                if search_term in site.lower() or search_term in username.lower():
                    hidden_password = "*" * 8  # Hide password with asterisks
                    item = self.tree.insert("", "end", values=("☐", site, username, hidden_password, date_added, date_edited, category, "👁"))
                    # Store the actual encrypted password in the tree item
                    self.tree.item(item, tags=(encrypted_password,))

        self.tree.column("Checkbox", width=30, anchor="center", stretch=False)
        self.tree.column("Site", width=200, anchor="w", stretch=True)
        for col in ("Username", "Password", "Date Added", "Date Edited", "Category"):
            self.tree.column(col, width=150, anchor="center", stretch=True)
        self.tree.column("Reveal", width=50, anchor="center", stretch=False)

    def toggle_checkbox(self, event):
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell":
            if column == "#1":
                item = self.tree.identify_row(event.y)
                if item:
                    current_values = self.tree.item(item, "values")
                    new_checkbox = "☑" if current_values[0] == "☐" else "☐"
                    self.tree.item(item, values=(new_checkbox,) + current_values[1:])
        if column == "#2": 
            self.on_double_click(event)
    
    def copy_to_clipboard(self, column_index):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = self.tree.item(selected_item)
        values = item['values']
        if values and column_index < len(values):
            copied_text = str(values[column_index])
            pyperclip.copy(copied_text)
            column_name = self.translate(self.tree['columns'][column_index])
            messagebox.showinfo(self.translate("Copied"), 
                                f"{column_name} {self.translate('copied to clipboard')}")
            
            threading.Timer(60, self.clear_clipboard_and_memory, args=[copied_text]).start()

    def clear_clipboard_and_memory(self, original_text):
        pyperclip.copy('')
        
        
        del original_text
        gc.collect()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def edit_password_content(self, stored_values=None):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if stored_values is None:
            messagebox.showwarning(self.translate("Warning"), self.translate("No password selected to edit"))
            self.update_content('view_passwords')
            return

        self.selected_item_values = stored_values
        site, username, password, date_added, date_edited, category = self.selected_item_values

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=self.translate('Edit Password'), font=("Helvetica", 20, "bold")).pack(pady=20)

        input_style = "TEntry"
        self.style.configure(input_style, padding=10)

        ttk.Label(frame, text=self.translate("Name/Website")).pack(pady=5)
        self.edit_site_entry = ttk.Entry(frame, style=input_style)
        self.edit_site_entry.insert(0, site)
        self.edit_site_entry.pack(pady=5, fill="x")

        ttk.Label(frame, text=self.translate("Username/Email")).pack(pady=5)
        username_frame = ttk.Frame(frame)
        username_frame.pack(pady=5, fill="x")
        self.edit_username_entry = ttk.Entry(username_frame, style=input_style)
        self.edit_username_entry.insert(0, username)
        self.edit_username_entry.pack(side="left", fill="x", expand=True)

        ttk.Label(frame, text=self.translate("Password")).pack(pady=5)
        password_frame = ttk.Frame(frame)
        password_frame.pack(pady=5, fill="x")
        self.edit_password_entry = ttk.Entry(password_frame, show="*", style=input_style)
        self.edit_password_entry.insert(0, password)
        self.edit_password_entry.pack(side="left", fill="x", expand=True)
        self.edit_show_password_var = tk.BooleanVar()
        eye_button = ttk.Checkbutton(password_frame, text="👁", command=self.toggle_edit_password_visibility, 
                                    variable=self.edit_show_password_var, style='info.Outline.TButton')
        eye_button.pack(side="right", padx=5)

         # Password strength meter
        self.edit_password_strength_frame = ttk.Frame(frame)
        self.edit_password_strength_frame.pack(pady=5, fill="x")
        self.edit_password_strength_label = ttk.Label(self.edit_password_strength_frame, text=self.translate("Password Strength:"))
        self.edit_password_strength_label.pack(side="left")
        self.edit_password_strength_meter = ttk.Progressbar(self.edit_password_strength_frame, length=200, mode='determinate')
        self.edit_password_strength_meter.pack(side="left", padx=5)

        # Password suggestions
        self.edit_password_suggestions_frame = ttk.Frame(frame)
        self.edit_password_suggestions_frame.pack(pady=5, fill="x")

        self.edit_password_entry.bind("<KeyRelease>", self.update_edit_password_strength)

        ttk.Label(frame, text=self.translate("Category")).pack(pady=5)
        categories = self.get_categories()
        self.category_var = tk.StringVar(value=category)
        category_dropdown = ttk.Combobox(frame, textvariable=self.category_var, values=categories, state="readonly")
        category_dropdown.pack(pady=5, fill="x")

        generate_button_frame = ttk.Frame(frame)
        generate_button_frame.pack(pady=10)

        generate_username_button = ttk.Button(generate_button_frame, text=self.translate("Generate Username"), 
                                    command=self.generate_and_insert_edit_username, bootstyle=(INFO, OUTLINE))
        generate_username_button.pack(side="left", padx=(0, 5))

        generate_password_button = ttk.Button(generate_button_frame, text=self.translate("Generate Password"), 
                                    command=self.generate_and_insert_edit_password, bootstyle=(INFO, OUTLINE))
        generate_password_button.pack(side="left", padx=(5, 0))

        self.edit_format_url_var = tk.BooleanVar()
        self.edit_format_url_checkbox = ttk.Checkbutton(frame, text=self.translate("Automatically add 'https://' and 'www.'"), 
                                                        variable=self.edit_format_url_var)
        self.edit_format_url_checkbox.pack(pady=5)

        ttk.Button(frame, text=self.translate("Save"), command=self.save_edited_password, bootstyle=SUCCESS).pack(pady=5)
        ttk.Button(frame, text=self.translate("Back"), command=lambda: self.update_content('view_passwords'), bootstyle=SECONDARY).pack(pady=5)

        self.update_edit_password_strength()

        self.auto_logout.reset()
        self.auto_logout.start()

    def toggle_edit_password_visibility(self):
        if self.edit_show_password_var.get():
            self.edit_password_entry.config(show="")
        else:
            self.edit_password_entry.config(show="*")

    def generate_and_insert_edit_password(self):
        password = generate_password()
        self.edit_password_entry.delete(0, tk.END)
        self.edit_password_entry.insert(0, password)
        self.update_edit_password_strength()

    def generate_and_insert_username(self):
        username = self.generate_username()
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)

    def generate_and_insert_edit_username(self):
        username = self.generate_username()
        self.edit_username_entry.delete(0, tk.END)
        self.edit_username_entry.insert(0, username)

    def generate_username(self):
        adjectives = self.load_words('adjectives')
        nouns = self.load_words('nouns')
        random_number = random.randint(10, 99)
        
        username = f"{random.choice(adjectives)}_{random.choice(nouns)}{random_number}"
        return username
        

    def save_edited_password(self):
        if not hasattr(self, 'selected_item_values'):
            messagebox.showwarning(self.translate("Warning"), self.translate("No password selected to edit"))
            return

        old_site, old_username, old_password, old_date_added, old_date_edited, old_category = self.selected_item_values

        site = str(self.edit_site_entry.get())
        username = str(self.edit_username_entry.get())
        password = self.edit_password_entry.get()
        category = self.category_var.get()

        if self.edit_format_url_var.get():
            site = format_url(site)

        # Checks if anything has changed
        if (site == old_site and 
            username == old_username and 
            password == old_password and
            category == old_category):
            messagebox.showinfo(self.translate("Info"), self.translate("No changes were made to the password entry"))
            self.update_content('view_passwords')
            return

        encrypted_password = encrypt_data(password, self.encryption_key)
        date_edited = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updated = False
        decrypt_file("passwords.json", self.encryption_key)
        with open("passwords.json", "r") as file:
            passwords = json.load(file)

        # Checks for duplicates and update the entry
        duplicate_found = False
        for entry in passwords:
            if entry["site"] == site and entry["username"] == username:
                if str(entry["site"]) != str(old_site) or str(entry["username"]) != str(old_username):
                    duplicate_found = True
                    break
            if str(entry["site"]) == str(old_site) and str(entry["username"]) == str(old_username):
                entry["site"] = site
                entry["username"] = username
                entry["current_password"] = encrypted_password.decode()
                entry["category"] = category
                entry["history"].append({
                    "password": encrypted_password.decode(),
                    "date": date_edited,
                    "site": site,
                    "username": username,
                    "category": category
                })
                updated = True
            
                self.expired_passwords.discard(f"{old_site} - {old_username}")
                self.expired_passwords.discard(f"{site} - {username}")

        if duplicate_found:
            messagebox.showwarning(self.translate("Warning"), 
                                self.translate("An entry with the same site and username already exists. No changes were made."))
            encrypt_file("passwords.json", self.encryption_key)
            return

        if updated:
            with open("passwords.json", "w") as file:
                json.dump(passwords, file, indent=2)
            encrypt_file("passwords.json", self.encryption_key)
            messagebox.showinfo(self.translate("Info"), self.translate("Password updated"))
        else:
            messagebox.showwarning(self.translate("Warning"), self.translate("Failed to update the password"))

        self.update_content('view_passwords')
        self.check_expired_passwords()

    def update_edit_password_strength(self, event=None):
        password = self.edit_password_entry.get()
        strength, color, suggestions = check_password_strength(password)
        translated_strength = self.translate(strength)
        self.edit_password_strength_label.config(text=f"{self.translate('Password Strength:')} {translated_strength}")

        if color == "red":
            value = 25
        elif color == "orange":
            value = 50
        elif color == "yellow":
            value = 75
        else:  
            value = 100
        
        self.edit_password_strength_meter['value'] = value
        self.edit_password_strength_meter['style'] = f"{color}.Horizontal.TProgressbar"

        self.update_edit_password_suggestions(suggestions)

    def update_edit_password_suggestions(self, suggestions):
        if hasattr(self, 'edit_suggestion_labels'):
            for label in self.edit_suggestion_labels:
                label.destroy()
        
        self.edit_suggestion_labels = []
        for suggestion in suggestions:
            label = ttk.Label(self.edit_password_strength_frame, text=f"• {self.translate(suggestion)}", font=("Helvetica", 10), foreground="gray")
            label.pack(anchor="w")
            self.edit_suggestion_labels.append(label)

    def delete_selected_passwords(self):
        selected_items = [item for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "☑"]
        if not selected_items:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select passwords to delete"))
            return

        if messagebox.askyesno(self.translate("Delete Passwords"), 
            self.translate("Are you sure you want to delete {0} selected passwords?").format(len(selected_items))):
            
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            
            deleted_count = 0
            passwords_to_keep = []
            for entry in passwords:
                should_delete = False
                for item in selected_items:
                    tree_values = self.tree.item(item, "values")
                    if str(entry["site"]) == str(tree_values[1]) and str(entry["username"]) == str(tree_values[2]):
                        should_delete = True
                        break
                if not should_delete:
                    passwords_to_keep.append(entry)
                else:
                    deleted_count += 1

            with open("passwords.json", "w") as file:
                json.dump(passwords_to_keep, file, indent=2)
            encrypt_file("passwords.json", self.encryption_key)
            
            # Removes deleted items from the treeview
            for item in selected_items:
                self.tree.delete(item)
            
            messagebox.showinfo(self.translate("Info"), 
                    self.translate("{0} passwords deleted").format(deleted_count))

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def view_password_history(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a password to view its history"))
            return

        item = self.tree.item(selected_item)
        current_site, current_username = map(str, item["values"][1:3])

        decrypt_file("passwords.json", self.encryption_key)
        with open("passwords.json", "r") as file:
            passwords = json.load(file)
        encrypt_file("passwords.json", self.encryption_key)

        # Finds the entry by matching either the current site/username or any historical site/username
        entry = next((p for p in passwords if 
                    (str(p["site"]) == current_site and str(p["username"]) == current_username) or
                    any(str(h.get("site")) == current_site and str(h.get("username")) == current_username for h in p.get("history", []))), 
                    None)

        if not entry:
            messagebox.showerror(self.translate("Error"), self.translate("Password entry not found"))
            return

        self.selected_item_values = item["values"]
        self.current_entry = entry

        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=f"{self.translate('Password History for')} {current_site} - {current_username}", font=("Helvetica", 16)).pack(pady=10)

        history_frame = ttk.Frame(frame)
        history_frame.pack(expand=True, fill="both")

        # Updates the columns order to match the view password screen
        columns = ("Site", "Username", "Password", "Date Added", "Category")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        for col in columns:
            self.history_tree.heading(col, text=self.translate(col))
            self.history_tree.column(col, width=150, anchor="center")

        self.history_tree.pack(side="left", expand=True, fill="both")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        for history_entry in reversed(entry["history"]):
            decrypted_password = decrypt_data(history_entry["password"].encode(), self.encryption_key)
            site = history_entry.get("site", entry["site"])
            username = history_entry.get("username", entry["username"])
            date_added = history_entry["date"]
            category = history_entry.get("category", "")
            self.history_tree.insert("", "end", values=(site, username, decrypted_password, date_added, category))

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=self.translate("Revert to Selected"), command=self.revert_to_selected_password, bootstyle=PRIMARY).pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Delete Selected"), command=self.delete_selected_history, bootstyle=DANGER).pack(side="left", padx=5)
        ttk.Button(button_frame, text=self.translate("Back"), command=lambda: self.update_content('view_passwords'), bootstyle=SECONDARY).pack(side="left", padx=5)

        self.auto_logout.reset()
        self.auto_logout.start()
    
    def revert_to_selected_password(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a password to revert to"))
            return

        item = self.history_tree.item(selected_item)
        site, username, password, date_added, category = item["values"]

        if messagebox.askyesno(self.translate("Confirm Revert"), self.translate("Are you sure you want to revert to this password?")):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)

            for entry in passwords:
                if entry == self.current_entry:
                    try:
                        encrypted_password = encrypt_data(password.encode('utf-8'), self.encryption_key)
                        entry["current_password"] = encrypted_password.decode('utf-8')
                    except AttributeError:
                        encrypted_password = encrypt_data(str(password).encode('utf-8'), self.encryption_key)
                        entry["current_password"] = encrypted_password.decode('utf-8')
                    
                    entry["site"] = site
                    entry["username"] = username
                    entry["category"] = category
                    entry["history"].append({
                        "password": entry["current_password"],
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "site": site,
                        "username": username,
                        "category": category
                    })
                    break

            with open("passwords.json", "w") as file:
                json.dump(passwords, file, indent=2)
            encrypt_file("passwords.json", self.encryption_key)

            messagebox.showinfo(self.translate("Success"), self.translate("Password reverted successfully"))
            self.view_passwords_content()

    def delete_selected_history(self):
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showwarning(self.translate("Warning"), self.translate("Please select a history entry to delete"))
            return

        item = self.history_tree.item(selected_item)
        selected_date = item["values"][3]

        # Checks if the selected entry is the current password
        if selected_date == self.current_entry["history"][-1]["date"]:
            messagebox.showwarning(self.translate("Warning"), self.translate("Cannot delete the current password entry"))
            return

        if messagebox.askyesno(self.translate("Confirm Deletion"), self.translate("Are you sure you want to delete this history entry?")):
            try:
                decrypt_file("passwords.json", self.encryption_key)
                with open("passwords.json", "r") as file:
                    passwords = json.load(file)

                for entry in passwords:
                    if (entry["site"] == self.current_entry["site"] and 
                        entry["username"] == self.current_entry["username"]):
                        entry["history"] = [h for h in entry["history"] if h["date"] != selected_date]
                        self.current_entry = entry  # Updates the current_entry
                        break

                with open("passwords.json", "w") as file:
                    json.dump(passwords, file, indent=2)
                encrypt_file("passwords.json", self.encryption_key)

                # Removes the selected item from the Treeview
                self.history_tree.delete(selected_item)

                messagebox.showinfo(self.translate("Success"), self.translate("History entry deleted successfully"))

                # Updates the Treeview if it's empty now
                if not self.history_tree.get_children():
                    self.view_passwords_screen()  # Go back to the main password view if there's no history left
            except Exception as e:
                messagebox.showerror(self.translate("Error"), f"{self.translate('An error occurred')}: {str(e)}")
                self.view_passwords_screen()

    def configure_styles(self):
        default_font = ("Helvetica", 12)
        self.style.configure('TLabel', font=default_font)
        self.style.configure('TButton', font=default_font)
        self.style.configure('TEntry', font=default_font)
        self.style.configure('TCheckbutton', font=default_font)
        self.style.configure('Treeview', font=default_font)
        self.style.configure('Treeview.Heading', font=("Helvetica", 12, "bold"))
        self.style.configure("red.Horizontal.TProgressbar", foreground="red", background="red")
        self.style.configure("orange.Horizontal.TProgressbar", foreground="orange", background="orange")
        self.style.configure("yellow.Horizontal.TProgressbar", foreground="yellow", background="yellow")
        self.style.configure("green.Horizontal.TProgressbar", foreground="green", background="green")


    def open_website(self, event):
        item = self.tree.selection()[0]
        site = self.tree.item(item, "values")[0]
        url = format_url(site)
        webbrowser.open(url)
    
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#2":
                item = self.tree.identify_row(event.y)
                if item:
                    site = self.tree.item(item, "values")[1]
                    url = format_url(site)
                    webbrowser.open(url)

    def on_tree_motion(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if item and column == "#2": 
            self.tree.config(cursor="hand2")
        else:
            self.tree.config(cursor="")

    def is_duplicate_entry(self, site, username, password, exclude_site=None, exclude_username=None):
        if os.path.exists("passwords.json"):
            decrypt_file("passwords.json", self.encryption_key)
            with open("passwords.json", "r") as file:
                passwords = json.load(file)
            encrypt_file("passwords.json", self.encryption_key)

            for entry in passwords:
                if exclude_site == entry["site"] and exclude_username == entry["username"]:
                    continue
                
                if (entry["site"] == site and 
                    entry["username"] == username and 
                    decrypt_data(entry["current_password"].encode(), self.encryption_key) == password):
                    return True
        return False

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.auto_logout.stop() 

    def on_closing(self):
        if hasattr(self, 'auto_logout'):
            self.auto_logout.cleanup()
        
        self.root.destroy()

        import sys
        sys.exit()
