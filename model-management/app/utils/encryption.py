"""
Encryption service for model file protection.

Uses Fernet symmetric encryption with support for key rotation.
"""

import base64
import logging
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class EncryptionService:
    """Service for encrypting and decrypting model files."""

    def __init__(self):
        """Initialize the encryption service."""
        self._fernet: Optional[Fernet] = None
        self._multi_fernet: Optional[MultiFernet] = None
        self._keys: list = []

    async def initialize(self) -> None:
        """
        Initialize encryption with keys.

        Loads existing keys or generates new ones.
        """
        if settings.ENCRYPTION_KEY:
            # Use key from environment variable
            key = settings.ENCRYPTION_KEY.encode()
            if len(key) != 44:  # Fernet key is 32 bytes, base64 encoded = 44 chars
                key = self._derive_key(settings.ENCRYPTION_KEY)
            self._keys = [key]
        elif os.path.exists(settings.ENCRYPTION_KEY_PATH):
            # Load keys from file
            self._keys = await self._load_keys_from_file()
        else:
            # Generate new key
            key = Fernet.generate_key()
            self._keys = [key]
            await self._save_keys_to_file()

        # Create Fernet instances
        fernets = [Fernet(key) for key in self._keys]
        self._fernet = fernets[0]  # Primary key
        self._multi_fernet = MultiFernet(fernets)  # All keys for rotation support

        logger.info("Encryption service initialized")

    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a Fernet key from a password.

        Args:
            password: Password to derive key from
            salt: Optional salt for key derivation

        Returns:
            Fernet-compatible key
        """
        if salt is None:
            salt = b"model-management-salt"  # Default salt for consistency

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    async def _load_keys_from_file(self) -> list:
        """
        Load encryption keys from file.

        Returns:
            List of encryption keys
        """
        async with aiofiles.open(settings.ENCRYPTION_KEY_PATH, "rb") as f:
            content = await f.read()
            keys = content.strip().split(b"\n")
            return keys

    async def _save_keys_to_file(self) -> None:
        """Save encryption keys to file."""
        key_path = Path(settings.ENCRYPTION_KEY_PATH)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(settings.ENCRYPTION_KEY_PATH, "wb") as f:
            await f.write(b"\n".join(self._keys))

        # Secure the key file
        os.chmod(settings.ENCRYPTION_KEY_PATH, 0o600)

    async def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file.

        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted file (optional)

        Returns:
            Path to encrypted file
        """
        if self._fernet is None:
            await self.initialize()

        if output_path is None:
            output_path = f"{input_path}.encrypted"

        logger.info(f"Encrypting file: {input_path}")

        # Read file in chunks for large files
        chunk_size = 64 * 1024 * 1024  # 64MB chunks

        async with aiofiles.open(input_path, "rb") as f_in:
            async with aiofiles.open(output_path, "wb") as f_out:
                while True:
                    chunk = await f_in.read(chunk_size)
                    if not chunk:
                        break

                    encrypted_chunk = self._fernet.encrypt(chunk)
                    # Write length prefix for chunk boundaries
                    chunk_len = len(encrypted_chunk).to_bytes(8, byteorder="big")
                    await f_out.write(chunk_len + encrypted_chunk)

        logger.info(f"File encrypted: {output_path}")
        return output_path

    async def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file.

        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted file (optional)

        Returns:
            Path to decrypted file

        Raises:
            InvalidToken: If decryption fails
        """
        if self._multi_fernet is None:
            await self.initialize()

        if output_path is None:
            output_path = input_path.replace(".encrypted", "")
            if output_path == input_path:
                output_path = f"{input_path}.decrypted"

        logger.info(f"Decrypting file: {input_path}")

        async with aiofiles.open(input_path, "rb") as f_in:
            async with aiofiles.open(output_path, "wb") as f_out:
                while True:
                    # Read chunk length
                    chunk_len_bytes = await f_in.read(8)
                    if not chunk_len_bytes:
                        break

                    chunk_len = int.from_bytes(chunk_len_bytes, byteorder="big")
                    encrypted_chunk = await f_in.read(chunk_len)

                    # MultiFernet tries all keys for rotation support
                    decrypted_chunk = self._multi_fernet.decrypt(encrypted_chunk)
                    await f_out.write(decrypted_chunk)

        logger.info(f"File decrypted: {output_path}")
        return output_path

    async def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt raw data.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if self._fernet is None:
            await self.initialize()

        return self._fernet.encrypt(data)

    async def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt raw data.

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data

        Raises:
            InvalidToken: If decryption fails
        """
        if self._multi_fernet is None:
            await self.initialize()

        return self._multi_fernet.decrypt(encrypted_data)

    async def rotate_key(self) -> str:
        """
        Rotate encryption key.

        Generates a new primary key while keeping old keys for decryption.

        Returns:
            New key identifier
        """
        # Generate new key
        new_key = Fernet.generate_key()

        # Add to beginning of key list (becomes primary)
        self._keys.insert(0, new_key)

        # Keep only last N keys
        max_keys = 5
        if len(self._keys) > max_keys:
            self._keys = self._keys[:max_keys]

        # Update Fernet instances
        fernets = [Fernet(key) for key in self._keys]
        self._fernet = fernets[0]
        self._multi_fernet = MultiFernet(fernets)

        # Save updated keys
        await self._save_keys_to_file()

        key_id = base64.urlsafe_b64encode(new_key[:8]).decode()
        logger.info(f"Key rotated. New key ID: {key_id}")

        return key_id

    async def re_encrypt_file(self, file_path: str) -> Tuple[str, bool]:
        """
        Re-encrypt a file with the current primary key.

        Useful after key rotation to update old files.

        Args:
            file_path: Path to encrypted file

        Returns:
            Tuple of (output path, success status)
        """
        try:
            # Create temp file for decrypted data
            temp_path = f"{file_path}.temp"

            # Decrypt with any available key
            await self.decrypt_file(file_path, temp_path)

            # Re-encrypt with primary key
            await self.encrypt_file(temp_path, file_path)

            # Remove temp file
            os.remove(temp_path)

            logger.info(f"File re-encrypted: {file_path}")
            return file_path, True

        except Exception as e:
            logger.error(f"Failed to re-encrypt file {file_path}: {e}")
            return file_path, False

    def generate_key(self) -> bytes:
        """
        Generate a new Fernet key.

        Returns:
            New encryption key
        """
        return Fernet.generate_key()

    async def get_key_info(self) -> dict:
        """
        Get information about current encryption keys.

        Returns:
            Dictionary with key information
        """
        if not self._keys:
            return {"status": "not_initialized", "key_count": 0}

        return {
            "status": "initialized",
            "key_count": len(self._keys),
            "primary_key_id": base64.urlsafe_b64encode(self._keys[0][:8]).decode(),
            "rotation_supported": len(self._keys) > 1,
        }


# Global instance
encryption_service = EncryptionService()


async def get_encryption_service() -> EncryptionService:
    """
    FastAPI dependency to get encryption service.

    Returns:
        EncryptionService instance
    """
    if encryption_service._fernet is None:
        await encryption_service.initialize()
    return encryption_service
