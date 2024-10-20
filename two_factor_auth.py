import pyotp
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
import json
import os

class TwoFactorAuth:
    def __init__(self):
        self.totp = None
        self.trusted_devices_file = "trusted_devices.json"

    def generate_secret(self):
        return pyotp.random_base32()

    def get_totp(self, secret):
        return pyotp.TOTP(secret)

    def verify(self, token):
        if self.totp:
            return self.totp.verify(token)
        return False

    def generate_qr_code(self, secret, username, box_size=5, border=4):
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(username, issuer_name="WyvernGuard")
        qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def trust_device(self, device_id, duration_days):
        expiry_date = datetime.now() + timedelta(days=duration_days)
        trusted_devices = self.load_trusted_devices()
        trusted_devices[device_id] = expiry_date.isoformat()
        self.save_trusted_devices(trusted_devices)

    def is_device_trusted(self, device_id):
        trusted_devices = self.load_trusted_devices()
        if device_id in trusted_devices:
            expiry_date = datetime.fromisoformat(trusted_devices[device_id])
            if expiry_date > datetime.now():
                return True
            else:
                del trusted_devices[device_id]
                self.save_trusted_devices(trusted_devices)
        return False

    def load_trusted_devices(self):
        if os.path.exists(self.trusted_devices_file):
            with open(self.trusted_devices_file, 'r') as f:
                return json.load(f)
        return {}

    def save_trusted_devices(self, trusted_devices):
        with open(self.trusted_devices_file, 'w') as f:
            json.dump(trusted_devices, f)