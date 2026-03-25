import os
import json
from cryptography.fernet import Fernet

class MetadataValidator:
    def __init__(self, encryption_key_path):
        self.encryption_key_path = encryption_key_path
        self.encryption_key = self.load_encryption_key()

    def load_encryption_key(self):
        with open(self.encryption_key_path, 'rb') as f:
            return f.read()

    def validate_metadata(self, metadata_file_path):
        with open(metadata_file_path, 'rb') as f:
            encrypted_metadata = f.read()

        fernet = Fernet(self.encryption_key)
        try:
            decrypted_metadata = fernet.decrypt(encrypted_metadata)
            metadata = json.loads(decrypted_metadata)
            # Validate the metadata structure and content here
            return metadata
        except (ValueError, json.JSONDecodeError, cryptography.fernet.InvalidToken):
            return None
