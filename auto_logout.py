import threading
import time

class AutoLogout:
    def __init__(self, timeout, logout_callback):
        self.timeout = timeout
        self.logout_callback = logout_callback
        self.timer = None
        self.active = False

    def reset(self):
           if self.timer is not None:
               self.timer.cancel()  # Cancels the existing timer
           self.timer = threading.Timer(self.timeout, self.logout)
           self.timer.start()

    def check_inactivity(self):
        if self.running and time.time() - self.last_activity > self.timeout:
            self.logout_callback()
        elif self.running:
            self.reset()

    def start(self):
        self.active = True
        self.reset()

    def stop(self):
           self.active = False
           if self.timer is not None:
               self.timer.cancel()

    def logout(self):
        if self.active:
            print("Logging out due to inactivity.")
            self.logout_callback()

    def cleanup(self):
        self.stop()
        if self.timer and self.timer.is_alive():
            self.timer.join(timeout=1.0)
    
    