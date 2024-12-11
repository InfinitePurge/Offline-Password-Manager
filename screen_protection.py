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
        
        self.start_protection()

    def create_blur_overlay(self):
        """Creates a full-screen blurred overlay."""
        if self.overlay_window:
            return
            
        # Take screenshot and blur it
        screenshot = ImageGrab.grab()
        blurred_screen = screenshot.filter(ImageFilter.GaussianBlur(radius=10))
        self.tk_blurred_image = ImageTk.PhotoImage(blurred_screen)
        
        # Create overlay window
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.attributes('-fullscreen', True, '-alpha', 0.5, '-topmost', True)
        self.overlay_window.overrideredirect(True)
        
        # Create and pack label
        label = tk.Label(self.overlay_window, image=self.tk_blurred_image)
        label.image = self.tk_blurred_image
        label.pack()
        
        # Schedule removal
        self.root.after(2000, self.remove_blur_overlay)

    def remove_blur_overlay(self):
        """Closes the overlay window if it is open."""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.tk_blurred_image = None

    def show_blur_overlay(self):
        """Shows blur overlay using the main thread."""
        self.root.after(0, self.create_blur_overlay)

    def process_image(self, path):
        """Process and blur saved screenshot files."""
        current_time = time.time()
        
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

    def on_created(self, event):
        """Handle new file creation events."""
        if not event.is_directory:
            self.process_image(event.src_path)
            
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.process_image(event.src_path)

    def check_clipboard_for_image(self):
        """Monitor clipboard for screenshots."""
        last_content = None
        last_check_time = 0
        check_interval = 0.1
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_check_time < check_interval:
                time.sleep(0.01)
                continue
                
            try:
                win32clipboard.OpenClipboard()
                
                formats_to_check = [
                    win32clipboard.CF_BITMAP,
                    win32clipboard.CF_DIB,
                    win32clipboard.CF_DIBV5
                ]
                
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

    def on_key_press(self, key):
        """Handle screenshot hotkey detection."""
        try:
            if key == keyboard.Key.print_screen or \
            (hasattr(key, 'vk') and key.vk == keyboard.Key.print_screen.vk and 
                keyboard.Key.alt in keyboard._pressed):
                print("Screenshot key combination detected")
                # Add a small delay to let the system capture the screenshot first
                time.sleep(0.1)
                # Then blur both the screen and the clipboard content
                self.show_blur_overlay()
                # Get and blur clipboard content
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
                    print(f"Error processing PrintScreen clipboard: {e}")
        except AttributeError:
            pass

    def setup_file_monitoring(self):
        """Setup file system monitoring for screenshot folders."""
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

    def start_protection(self):
        """Start all screenshot prevention mechanisms."""
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

    def stop_protection(self):
        """Stop all screenshot prevention mechanisms."""
        self.running = False
        
        if self.listener:
            self.listener.stop()
            
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            
        self.remove_blur_overlay()
        print("Screenshot protection stopped")