import face_recognition
import cv2
import numpy as np
import os
import io
import json
from cryptography.fernet import Fernet
import uuid
import base64
import logging
from pathlib import Path
from PIL import Image
import win32security
import win32api
import win32con
import ntsecuritycon as con

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class FaceRecognitionAuth:
    def __init__(self):
        self.user_face_encoding = None
        self.face_image_path = "user_face_hidden.png"
        self.settings_path = "face_recognition_settings.json"
        self.key_path = "face_recognition.key"
        self.backup_folder = Path(os.getenv('APPDATA')) / "WyvernGuard"
        self.backup_face_image_path = self.backup_folder / "backup_user_face_hidden.png"
        self.create_secure_backup_folder()
        self.load_key()
        self.load_settings()
        self.load_face_data()

    def load_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as key_file:
                self.key = key_file.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(self.key)
        self.cipher_suite = Fernet(self.key)

    def enable_face_recognition(self, image_data):
        face_image = face_recognition.load_image_file(io.BytesIO(image_data))
        face_encodings = face_recognition.face_encodings(face_image)
        
        if len(face_encodings) > 0:
            self.user_face_encoding = face_encodings[0]
            self.save_face_data(image_data)
            self.save_settings(True)
            return True
        else:
            return False
        
    def create_secure_backup_folder(self):
        if not self.backup_folder.exists():
            self.backup_folder.mkdir(parents=True, exist_ok=True)
        
        # Get the SID of the Administrators group
        admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
        
        # Get the SID of the current user
        current_user_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
            win32security.TokenUser
        )[0]
        
        # Create a new DACL (Discretionary Access Control List)
        dacl = win32security.ACL()
        
        # Add ACEs (Access Control Entries) to the DACL
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, admins_sid)
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, current_user_sid)
        
        # Set the DACL on the folder
        win32security.SetNamedSecurityInfo(
            str(self.backup_folder),
            win32security.SE_FILE_OBJECT,
            win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
            None, None, dacl, None
        )
        
        logging.debug(f"Secure backup folder created: {self.backup_folder}")
    
    def save_face_data(self, image_data):
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((200, 200))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        compressed_image_data = buffered.getvalue()

        face_data = self.user_face_encoding.tobytes()
        combined_data = face_data + b'|||' + compressed_image_data
        encrypted_data = self.cipher_suite.encrypt(combined_data)
        
        # Save to main file
        with open(self.face_image_path, "wb") as f:
            f.write(encrypted_data)
        logging.debug(f"Saved face data to main file: {self.face_image_path}")
        
        # Save to backup file with restricted permissions
        self.backup_folder.mkdir(parents=True, exist_ok=True)
        with open(self.backup_face_image_path, "wb") as f:
            f.write(encrypted_data)
        
        # Set restricted permissions on the backup file
        admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
        current_user_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
            win32security.TokenUser
        )[0]
        
        dacl = win32security.ACL()
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, admins_sid)
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, current_user_sid)
        
        win32security.SetNamedSecurityInfo(
            str(self.backup_face_image_path),
            win32security.SE_FILE_OBJECT,
            win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
            None, None, dacl, None
        )
        
        logging.debug(f"Saved face data to backup file with restricted permissions: {self.backup_face_image_path}")

    def load_face_data(self):
        encrypted_data = self.get_encrypted_face_data()
        if encrypted_data:
            try:
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                parts = decrypted_data.split(b'|||')
                if len(parts) != 2:
                    raise ValueError("Invalid data format")
                
                face_data, _ = parts
                self.user_face_encoding = np.frombuffer(face_data, dtype=np.float64)
                logging.debug("Successfully loaded face data")
                return True
            except Exception as e:
                logging.error(f"Error loading face data: {str(e)}")
        else:
            logging.warning("No face data found")
        return False

    def get_encrypted_face_data(self):
        if os.path.exists(self.face_image_path):
            logging.debug(f"Loading face data from main file: {self.face_image_path}")
            with open(self.face_image_path, "rb") as f:
                return f.read()
        elif os.path.exists(self.backup_face_image_path):
            logging.debug(f"Loading face data from backup file: {self.backup_face_image_path}")
            with open(self.backup_face_image_path, "rb") as f:
                return f.read()
        logging.warning("No face data found in main or backup file")
        return None

    def get_original_face_image(self):
        encrypted_data = self.get_encrypted_face_data()
        if encrypted_data:
            try:
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                parts = decrypted_data.split(b'|||')
                if len(parts) != 2:
                    raise ValueError("Invalid data format")
                
                _, image_data = parts
                return image_data
            except Exception as e:
                logging.error(f"Error getting original face image: {str(e)}")
        return None

    def disable_face_recognition(self):
        if os.path.exists(self.face_image_path):
            os.remove(self.face_image_path)
            logging.debug(f"Removed main face data file: {self.face_image_path}")
        if os.path.exists(self.backup_face_image_path):
            os.remove(self.backup_face_image_path)
            logging.debug(f"Removed backup face data file: {self.backup_face_image_path}")
        self.user_face_encoding = None
        self.save_settings(False)
        logging.debug("Face recognition disabled")

    def verify_face(self, frame):
        if self.user_face_encoding is None:
            self.load_face_data()
        
        if self.user_face_encoding is None:
            logging.warning("No face encoding available for verification")
            return False

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces([self.user_face_encoding], face_encoding)
            if True in matches:
                logging.debug("Face verified successfully")
                return True
        logging.debug("Face not recognized")
        return False
    
    def save_settings(self, enabled):
        settings = {"enabled": enabled, "user_id": str(uuid.uuid4())}
        with open(self.settings_path, "w") as f:
            json.dump(settings, f)
        logging.debug(f"Saved face recognition settings: enabled={enabled}")

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r") as f:
                settings = json.load(f)
            if settings.get("enabled", False):
                logging.debug("Face recognition enabled in settings")
                return self.load_face_data()
        logging.debug("Face recognition not enabled in settings")
        return False

    def is_enabled(self):
        enabled = self.user_face_encoding is not None or self.load_face_data()
        logging.debug(f"Face recognition is_enabled: {enabled}")
        return enabled

    def capture_image_from_webcam(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Failed to open camera")
            return None

        try:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to capture frame")
                return None

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', rgb_frame)
            image_data = buffer.tobytes()

            return image_data
        except Exception as e:
            logging.error(f"Error capturing image: {str(e)}")
            return None
        finally:
            cap.release()