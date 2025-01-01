import tkinter as tk
from pynput import keyboard
import threading
import time
import win32clipboard
from PIL import ImageGrab, ImageFilter, ImageTk, Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import io

class ScreenProtection(FileSystemEventHandler):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.overlay_window = None
        self.listener = None
        self.file_observer = None
        self.clipboard_thread = None
        self.running = False
        self.last_processed_time = {}
        self.processing_cooldown = 1.0
        self.start_time = time.time()
        self.last_exported_file = None
        self.is_windows_11 = self.check_windows_version()
        self.screenshot_hotkeys = [
            keyboard.Key.print_screen,
            keyboard.KeyCode.from_vk(0x2C),  # Windows 11 uses VK_SNAPSHOT (0x2C)
            keyboard.KeyCode(vk=44)  # Alternative VK code for PrintScreen
        ]

    def check_windows_version(self):
        """Check if running on Windows 11"""
        try:
            import sys
            import platform
            if sys.platform == 'win32':
                version = platform.win32_ver()[0]
                return version.startswith('11')
        except:
            return False
        return False
        

    def create_blur_overlay(self):
        """Creates a full-screen blurred overlay."""
        if self.overlay_window:
            return
            
        # Screenshot blur
        screenshot = ImageGrab.grab()
        blurred_screen = screenshot.filter(ImageFilter.GaussianBlur(radius=10))
        self.tk_blurred_image = ImageTk.PhotoImage(blurred_screen)
        
        # Creates overlay window
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.attributes('-fullscreen', True, '-alpha', 0.5, '-topmost', True)
        self.overlay_window.overrideredirect(True)
        
        # Creats and packs label
        label = tk.Label(self.overlay_window, image=self.tk_blurred_image)
        label.image = self.tk_blurred_image
        label.pack()
        
        # Schedules removal
        self.root.after(2000, self.remove_blur_overlay)

        # Closes the overlay window if it is open.
    def remove_blur_overlay(self):
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.tk_blurred_image = None

    # Shows blur overlay using the main thread.
    def show_blur_overlay(self):
        self.root.after(0, self.create_blur_overlay)

    # Sets the path of the recently exported file to ignore.
    def set_exported_file(self, filepath):
        self.last_exported_file = os.path.abspath(filepath)

    # Processes and blurs saved screenshot files.
    def process_image(self, path):
        # Skips processing if this is the recently exported file
        if self.last_exported_file and os.path.abspath(path) == self.last_exported_file:
            return
            
        current_time = time.time()
        
        # Check if the file exists before processing
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return
        
        # Checks if the file was created or modified after the program started
        if os.path.getctime(path) < self.start_time and os.path.getmtime(path) < self.start_time:
            return
        
        if path in self.last_processed_time:
            if current_time - self.last_processed_time[path] < self.processing_cooldown:
                return
        
        file_ext = os.path.splitext(path)[1].lower()
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        
        if file_ext in image_extensions:
            try:
                img = Image.open(path)
                blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
                blurred.save(path)
                print(f"Blurred: {os.path.basename(path)}")
                self.last_processed_time[path] = current_time
            except Exception as e:
                print(f"Error processing {os.path.basename(path)}: {e}")

    def process_clipboard_image(self):
        """Separate method to handle clipboard image processing"""
        try:
            clipboard_image = ImageGrab.grabclipboard()
            if clipboard_image:
                blurred = clipboard_image.filter(ImageFilter.GaussianBlur(radius=10))
                output = io.BytesIO()
                blurred.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]
                output.close()
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Error processing clipboard image: {e}")

    # Handles new file creation events.
    def on_created(self, event):
        if not event.is_directory:
            self.process_image(event.src_path)
            
    # Handles file modification events.
    def on_modified(self, event):
        if not event.is_directory:
            self.process_image(event.src_path)

    def check_clipboard_for_image(self):
        last_content = None
        last_check_time = 0
        check_interval = 0.1

        # Define formats_to_check outside of the try block
        formats_to_check = [
            win32clipboard.CF_BITMAP,
            win32clipboard.CF_DIB,
            win32clipboard.CF_DIBV5
        ]

        # Initialize last_content with the current clipboard content
        try:
            win32clipboard.OpenClipboard()
            
            for format in formats_to_check:
                if win32clipboard.IsClipboardFormatAvailable(format):
                    last_content = format
                    break
        except Exception as e:
            print(f"Error accessing clipboard on startup: {e}")
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

        while self.running:
            current_time = time.time()
            
            if current_time - last_check_time < check_interval:
                time.sleep(0.01)
                continue
                
            try:
                win32clipboard.OpenClipboard()
                
                current_content = None
                for format in formats_to_check:
                    if win32clipboard.IsClipboardFormatAvailable(format):
                        current_content = format
                        break
                        
                if current_content and current_content != last_content:
                    print("Screenshot detected in clipboard")
                    # Get the image from clipboard
                    try:
                        clipboard_image = ImageGrab.grabclipboard()
                        if clipboard_image:
                            # Blur the clipboard image
                            blurred = clipboard_image.filter(ImageFilter.GaussianBlur(radius=10))
                            # Convert back to bitmap
                            output = io.BytesIO()
                            blurred.convert('RGB').save(output, 'BMP')
                            data = output.getvalue()[14:]  # Skip bitmap header
                            output.close()
                            # Clear clipboard and set new content
                            win32clipboard.EmptyClipboard()
                            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    except Exception as e:
                        print(f"Error processing clipboard image: {e}")
                    
                    self.show_blur_overlay()
                    
                last_content = current_content
                
            except Exception as e:
                if "cannot open clipboard" not in str(e).lower():
                    print(f"Clipboard error: {e}")
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                
            last_check_time = current_time

    # Apdoroja ekrano kopijos klavišų (angl:. Print Screen) paspaudimą
    def on_key_press(self, key):
        try:
            # Enhanced screenshot detection for both Windows 10 and 11
            is_screenshot_key = (
                key in self.screenshot_hotkeys or
                (hasattr(key, 'vk') and key.vk in [k.vk for k in self.screenshot_hotkeys if hasattr(k, 'vk')])
            )
            
            if is_screenshot_key or (
                hasattr(key, 'vk') and 
                keyboard.Key.alt in keyboard._pressed
            ):
                print(f"Screenshot key detected on {'Windows 11' if self.is_windows_11 else 'Windows 10'}")
                self.start_protection()
                
                # Increased delay for Windows 11
                time.sleep(0.2 if self.is_windows_11 else 0.1)
                self.show_blur_overlay()
                
                # Add multiple attempts for Windows 11
                if self.is_windows_11:
                    max_attempts = 3
                    for _ in range(max_attempts):
                        try:
                            self.process_clipboard_image()
                            break
                        except Exception as e:
                            print(f"Attempt to process clipboard failed: {e}")
                            time.sleep(0.1)
                else:
                    self.process_clipboard_image()
                    
        except AttributeError:
            pass

    # Sets up file system monitoring for screenshot folders.
    def setup_file_monitoring(self):
        paths_to_monitor = [
            os.path.join(os.path.expanduser('~'), 'Pictures', 'Screenshots'),
            os.path.join(os.path.expanduser('~'), 'Pictures'),
            os.path.join(os.path.expanduser('~'), 'Desktop'),
            os.path.join(os.path.expanduser('~'), 'Downloads'),
        ]
        
        observer = Observer()
        for path in paths_to_monitor:
            if os.path.exists(path):
                observer.schedule(self, path, recursive=False)
                print(f"Monitoring: {path}")
        
        return observer

    # Starts all screenshot prevention mechanisms.
    def start_protection(self):
        self.running = True
        
        # Start keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        # Start clipboard monitoring thread
        self.clipboard_thread = threading.Thread(
            target=self.check_clipboard_for_image, 
            daemon=True
        )
        self.clipboard_thread.start()

        # Start file system monitoring
        self.file_observer = self.setup_file_monitoring()
        self.file_observer.start()
        
        print("Screenshot protection active")

    # Stops all screenshot prevention mechanisms.
    def stop_protection(self):
        self.running = False

        if self.listener:
            self.listener.stop()
            
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            
        self.remove_blur_overlay()
        print("Screenshot protection stopped")