import os
import hmac
import hashlib

# Relative path resolution that works from any execution context
MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(MODELS_DIR)
SAVED_MODELS_DIR = os.path.join(BACKEND_DIR, "saved_models")

def get_secret_key():
    """
    Retrieves the HMAC secret key.
    Checks environment variable 'HMAC_SECRET_KEY' first.
    If not set, falls back to a persistent local key file in the saved_models folder.
    """
    key_env = os.getenv("HMAC_SECRET_KEY")
    if key_env:
        return key_env.encode('utf-8')
        
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
    key_path = os.path.join(SAVED_MODELS_DIR, ".hmac_key")
    
    if os.path.exists(key_path):
        try:
            with open(key_path, "rb") as f:
                key = f.read()
                if len(key) >= 32:
                    return key
        except Exception as e:
            print(f"Error reading persistent HMAC key: {e}")
            
    # Generate new persistent 32-byte key
    new_key = os.urandom(32)
    try:
        with open(key_path, "wb") as f:
            f.write(new_key)
        # On Windows, try to hide the file
        if os.name == 'nt':
            import ctypes
            try:
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 2) # FILE_ATTRIBUTE_HIDDEN
            except Exception:
                pass
    except Exception as e:
        print(f"Error writing persistent HMAC key: {e}")
        
    return new_key

def calculate_signature(file_path: str) -> str:
    """
    Computes the HMAC-SHA256 signature of a file's contents.
    """
    key = get_secret_key()
    h = hmac.new(key, digestmod=hashlib.sha256)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def sign_file(file_path: str) -> str:
    """
    Generates a companion signature file (.sig) for the target file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot sign non-existent file: {file_path}")
        
    sig = calculate_signature(file_path)
    sig_path = file_path + ".sig"
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(sig)
    print(f"SecureCoder: Generated signature for {os.path.basename(file_path)}")
    return sig

def verify_signature(file_path: str) -> bool:
    """
    Validates a file against its companion signature (.sig) using hmac.compare_digest.
    Raises PermissionError if signature mismatch is detected, preventing deserialization.
    """
    sig_path = file_path + ".sig"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model file not found: {file_path}")
        
    if not os.path.exists(sig_path):
        raise PermissionError(
            f"Security Error: Signature verification failed for {os.path.basename(file_path)}! "
            f"No signature file (.sig) found. Deserialization aborted."
        )
        
    try:
        with open(sig_path, "r", encoding="utf-8") as f:
            expected_sig = f.read().strip()
    except Exception as e:
        raise PermissionError(f"Security Error: Unable to read signature file for {os.path.basename(file_path)}: {e}")
        
    actual_sig = calculate_signature(file_path)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise PermissionError(
            f"Security Violation: HMAC signature mismatch detected for {os.path.basename(file_path)}! "
            f"The model file has been modified, corrupted, or tampered with. Deserialization blocked."
        )
        
    return True
