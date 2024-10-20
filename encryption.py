from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Log an informational message
def log_info(message):
    logging.info(message)

# Generates a new Fernet key and saves it to a file
def generate_key():
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)

# Loads the Fernet key from a file
def load_key():
    return open("key.key", "rb").read()

# Generates a new salt and saves it to a file
def generate_salt():
    return os.urandom(16)

# Saves the salt to a file
def save_salt(salt):
    with open("salt.bin", "wb") as salt_file:
        salt_file.write(salt)

# Loads the salt from a file
def load_salt():
    with open("salt.bin", "rb") as salt_file:
        return salt_file.read()

# Derives a key from a password and salt
def derive_key(password, salt):
    if isinstance(password, str):
        password = password.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=1000000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

# Generates and saves a key for a master password
def generate_and_save_key(master_password):
    salt = generate_salt()
    save_salt(salt)
    key = derive_key(master_password, salt)
    fernet_key = Fernet.generate_key()
    encrypted_key = Fernet(ensure_fernet_key(key)).encrypt(fernet_key)
    with open("key.key", "wb") as key_file:
        key_file.write(encrypted_key)
    return fernet_key

# Loads the key for a master password
def load_key(master_password):
    try:
        salt = load_salt()
        key = derive_key(master_password, salt)
        with open("key.key", "rb") as key_file:
            encrypted_key = key_file.read()
        return Fernet(ensure_fernet_key(key)).decrypt(encrypted_key)
    except Exception as e:
        print(f"Error loading key: {e}")
        raise

# Ensures the data is in bytes
def ensure_bytes(data):
    if isinstance(data, str):
        return data.encode('utf-8')
    return data

# Ensures the key is a valid Fernet key
def ensure_fernet_key(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    if len(key) != 32:
        key = base64.urlsafe_b64encode(key.ljust(32)[:32])
    return key

# Encrypts data using a key
def encrypt_data(data, key):
    data = ensure_bytes(data)
    key = ensure_fernet_key(key)
    fernet = Fernet(key)
    
    nonce = os.urandom(16)
    
    # Preped the nonce to the data
    obfuscated_data = nonce + data
    
    encrypted_data = fernet.encrypt(obfuscated_data)
    return encrypted_data

# Decrypts data using a key
def decrypt_data(encrypted_data, key):
    def decrypt_with_key(k):
        k = ensure_fernet_key(k)
        fernet = Fernet(k)
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Extract the nonce and the original data
        nonce = decrypted_data[:16]
        original_data = decrypted_data[16:]
        
        try:
            return original_data.decode('utf-8')
        except UnicodeDecodeError:
            return original_data

    return use_key_securely(key, decrypt_with_key)

# Encrypts a file using a key
def encrypt_file(file_path, key):
    with open(file_path, 'rb') as file:
        data = file.read()
    encrypted_data = encrypt_data(data.decode(), key)
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)

# Decrypts a file using a key
def decrypt_file(file_path, key):
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    decrypted_data = decrypt_data(encrypted_data, key)
    with open(file_path, 'wb') as file:
        file.write(decrypted_data.encode())

# Securely erases data
def secure_erase(data):
    if isinstance(data, bytes):
        length = len(data)
        for _ in range(3):  # Overwrites 3 times
            data[:] = os.urandom(length)
    elif isinstance(data, bytearray):
        length = len(data)
        for _ in range(3): 
            data[:] = bytearray(os.urandom(length))
    elif isinstance(data, str):
        length = len(data)
        for _ in range(3):
            data = ''.join(chr(os.urandom(1)[0]) for _ in range(length))
    del data

# Securely erases a string
def secure_string_erase(s):
    return ''.join(chr(os.urandom(1)[0]) for _ in range(len(s)))

# Uses a key securely
def use_key_securely(key, func):
    try:
        return func(key)
    finally:
        key = secure_string_erase(key)
        del key

# Generates a time-based key
def generate_time_based_key(master_key, time_interval=3600):
    current_time = int(time.time())
    time_factor = current_time // time_interval
    log_info(f"Generating time-based key. Time factor: {time_factor}")
    if isinstance(master_key, str):
        master_key = master_key.encode()
    combined_key = master_key + str(time_factor).encode()
    return derive_key(combined_key, load_salt())

# Encrypts data with time-based key rotation
def encrypt_data_with_rotation(data, master_key, time_interval=3600):
    rotated_key = generate_time_based_key(master_key, time_interval)
    log_info(f"Encrypting data. Key length: {len(rotated_key)}")
    encrypted = encrypt_data(data, rotated_key)
    log_info(f"Data encrypted. Ciphertext length: {len(encrypted)}")
    return encrypted

# Decrypts data with time-based key rotation
def decrypt_data_with_rotation(encrypted_data, master_key, time_interval=3600):
    def decrypt_with_rotated_key(mk):
        try:
            rotated_key = generate_time_based_key(mk, time_interval)
            log_info(f"Decrypting data. Key length: {len(rotated_key)}")
            decrypted = decrypt_data(encrypted_data, rotated_key)
            log_info(f"Data decrypted. Plaintext length: {len(decrypted)}")
            if isinstance(decrypted, bytes):
                return decrypted.decode('utf-8')
            return decrypted
        except Exception as e:
            log_info(f"Error in decrypt_with_rotated_key: {str(e)}")
            raise

    return use_key_securely(master_key, decrypt_with_rotated_key)

# Changes the master password
def change_master_password(old_password, new_password):
    try:
        print("Attempting to change master password...")
        # Verifies old password
        if not validate_master_password(old_password):
            print("Old password is incorrect.")
            return False

        # Generates new salt and key
        new_salt = generate_salt()
        save_salt(new_salt)
        print("New salt generated and saved.")
        
        new_key = derive_key(new_password, new_salt)
        print(f"New key derived. Type: {type(new_key)}, Length: {len(new_key)}")
        
        # Generates a new Fernet key
        new_fernet_key = Fernet.generate_key()
        print(f"New Fernet key generated. Length: {len(new_fernet_key)}")
        
        # Encrypt the new Fernet key with the derived key
        encrypted_new_key = Fernet(ensure_fernet_key(new_key)).encrypt(new_fernet_key)
        print(f"New Fernet key encrypted. Length: {len(encrypted_new_key)}")
        
        # Saves the encrypted new key
        with open("key.key", "wb") as key_file:
            key_file.write(encrypted_new_key)
        print("New encrypted key saved.")
        
        return True
    except Exception as e:
        print(f"Error changing master password: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Validates the master password
def validate_master_password(master_password):
    try:
        load_key(master_password)
        return True
    except Exception as e:
        print(f"Password validation failed: {str(e)}")
        return False