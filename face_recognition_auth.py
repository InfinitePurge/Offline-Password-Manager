import face_recognition
import cv2
import numpy as np
import os
from PIL import Image
import io
import json
from cryptography.fernet import Fernet
from stegano import lsb
import uuid
import base64

class FaceRecognitionAuth:
    def __init__(self):
        self.user_face_encoding = None
        self.face_image_path = "user_face_hidden.png"
        self.original_face_image_path = "user_face_original.jpg"
        self.settings_path = "face_recognition_settings.json"
        self.key_path = "face_recognition.key"
        self.load_key()
        self.load_settings()

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
    
    def disable_face_recognition(self):
        if os.path.exists(self.face_image_path):
            os.remove(self.face_image_path)
        self.user_face_encoding = None
        self.save_settings(False)

    def verify_face(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)

        ret, frame = self.cap.read()
        if not ret:
            return False

        # Converts the image from BGR color (which OpenCV uses) to RGB color
        rgb_frame = frame[:, :, ::-1]

        # Finds all the faces in the current frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            # Compares the face with the stored user face
            matches = face_recognition.compare_faces([self.user_face_encoding], face_encoding)

            if True in matches:
                return True

        return False
    
    def save_face_data(self, image_data):
        # Compresses the image
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((200, 200))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        compressed_image_data = buffered.getvalue()

        # Converts face encoding to bytes
        face_data = self.user_face_encoding.tobytes()
        
        # Combines face data and compressed image data
        combined_data = face_data + b'|||' + compressed_image_data
        
        # Encrypts the combined data
        encrypted_data = self.cipher_suite.encrypt(combined_data)
        
        # Saves the encrypted data to a file
        with open(self.face_image_path, "wb") as f:
            f.write(encrypted_data)

    def load_face_data(self):
        if os.path.exists(self.face_image_path):
            try:
                with open(self.face_image_path, "rb") as f:
                    encrypted_data = f.read()
                
                # Decrypts the data
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
                # Splits the combined data
                parts = decrypted_data.split(b'|||')
                if len(parts) != 2:
                    raise ValueError("Invalid data format")
                
                face_data, _ = parts
                
                # Converts bytes back to numpy array
                self.user_face_encoding = np.frombuffer(face_data, dtype=np.float64)
                return True
            except Exception as e:
                print(f"Error loading face data: {str(e)}")
                return False
        return False

    def get_original_face_image(self):
        if os.path.exists(self.face_image_path):
            try:
                with open(self.face_image_path, "rb") as f:
                    encrypted_data = f.read()
                
                # Decrypts the data
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
                # Splits the combined data
                parts = decrypted_data.split(b'|||')
                if len(parts) != 2:
                    raise ValueError("Invalid data format")
                
                _, image_data = parts
                
                return image_data
            except Exception as e:
                print(f"Error getting original face image: {str(e)}")
                return None
        return None

    def disable_face_recognition(self):
        if os.path.exists(self.face_image_path):
            os.remove(self.face_image_path)
        self.user_face_encoding = None
        self.save_settings(False)

    def verify_face(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces([self.user_face_encoding], face_encoding)
            if True in matches:
                return True
        return False
    
    def get_face_image(self):
        if os.path.exists(self.face_image_path):
            with open(self.face_image_path, "rb") as f:
                return f.read()
        return None

    def save_settings(self, enabled):
        settings = {"enabled": enabled, "user_id": str(uuid.uuid4())}
        with open(self.settings_path, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r") as f:
                settings = json.load(f)
            if settings.get("enabled", False):
                return self.load_face_data()
        return False

    def is_enabled(self):
        return self.user_face_encoding is not None

    def capture_image_from_webcam(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Failed to open camera")
            return None

        try:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                return None

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', rgb_frame)
            image_data = buffer.tobytes()

            return image_data
        except Exception as e:
            print(f"Error capturing image: {str(e)}")
            return None
        finally:
            cap.release()
    
    def __del__(self):
        if self.cap is not None:
            self.cap.release()