import encryption as enc
import time

def test_encryption_system():
    enc.log_info("Starting encryption system test")

    # Test data
    original_data = "This is a secret message."
    master_password = "test_password"

    enc.log_info(f"Original data: {original_data}")

    # Generate and save key
    enc.generate_and_save_key(master_password)
    enc.log_info("Key generated and saved.")

    # Simulate multiple runs
    for i in range(3):
        enc.log_info(f"\nRun {i+1}:")
        
        # Load key and encrypt data
        key = enc.load_key(master_password)
        encrypted_data = enc.encrypt_data_with_rotation(original_data.encode(), key)
        enc.log_info(f"Encrypted data: {encrypted_data}")

        # Decrypt data
        decrypted_data = enc.decrypt_data_with_rotation(encrypted_data, key)
        enc.log_info(f"Decrypted data: {decrypted_data}")

        # Wait for a short time to simulate time passing
        time.sleep(2)

    enc.log_info("Encryption system test completed")

if __name__ == "__main__":
    test_encryption_system()