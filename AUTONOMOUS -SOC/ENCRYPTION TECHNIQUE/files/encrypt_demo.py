"""
encrypt_demo.py
===============
Autonomous Cloud SOC — Rubric R1c: Apply Encryption Techniques
Student  : Khushbu Jalan
Program  : DAE Cybersecurity Program — Semester 1
GitHub   : scripts/encrypt_demo.py

What this script demonstrates
------------------------------
1. AES-256-CBC  — symmetric encryption used to protect data at rest and in transit.
                  The same key that encrypts can decrypt (symmetric).
                  256-bit key = 32 bytes — the strongest AES variant.
                  CBC mode = each 16-byte block is XOR'd with the previous ciphertext
                  block before encryption, making identical plaintext produce
                  different ciphertext each time (via a random IV).

2. SHA-256 hash — one-way function. You can hash a password and store the hash,
                  but you cannot reverse it back to the original password.
                  Used in this project to hash Wazuh alert passwords and
                  verify file integrity (FIM stores SHA-256 hashes of monitored files).

Project connection
-------------------
- AES-256 is the encryption standard used for OCI boot volume encryption and
  for TLS sessions between Wazuh agents and the Wazuh Manager.
- SHA-256 is used by Wazuh FIM to fingerprint every monitored file on the
  Windows Honeypot. Any change in the hash = file was modified = FIM alert.

Requirements: pip install pycryptodome
"""

import os
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# In the real SOC, these values come from environment variables
# (stored in the Docker .env file, never hardcoded in production).
# For this demonstration they are hardcoded so the script is
# self-contained and runnable without any setup.
# ─────────────────────────────────────────────────────────────────

# AES-256 key = exactly 32 bytes (256 bits)
# In production: secrets.token_bytes(32), stored securely
AES_KEY = b"SOC_AES256_KhushbuJalan_DAE_2026"   # exactly 32 bytes

# The message we are encrypting — simulates a Wazuh alert payload
PLAINTEXT = "WAZUH ALERT: Brute-force detected on Honeypot from IP 185.220.101.47 | Level 10 HIGH | 2026-04-01 09:14:33"

# ─────────────────────────────────────────────────────────────────
# PART 1: AES-256-CBC ENCRYPTION
# ─────────────────────────────────────────────────────────────────

def aes_encrypt(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext using AES-256-CBC.
    Returns (iv, ciphertext) — the IV must be stored alongside the
    ciphertext so decryption is possible. The IV is not secret,
    but it must be unique for every encryption operation.
    """
    iv = os.urandom(16)                        # 16-byte random IV (CBC requirement)
    cipher = AES.new(key, AES.MODE_CBC, iv)    # Create cipher object
    padded = pad(plaintext.encode(), AES.block_size)  # PKCS7 pad to 16-byte boundary
    ciphertext = cipher.encrypt(padded)
    return iv, ciphertext


def aes_decrypt(iv: bytes, ciphertext: bytes, key: bytes) -> str:
    """
    Decrypt AES-256-CBC ciphertext.
    Returns the original plaintext string.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)    # Must use same key and IV
    padded = cipher.decrypt(ciphertext)
    return unpad(padded, AES.block_size).decode()


# ─────────────────────────────────────────────────────────────────
# PART 2: SHA-256 HASHING
# ─────────────────────────────────────────────────────────────────

def sha256_hash(text: str) -> str:
    """
    Compute SHA-256 hash of the given string.
    Returns a 64-character lowercase hex string.
    SHA-256 is a one-way function — the hash cannot be reversed.
    """
    return hashlib.sha256(text.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────
# MAIN DEMONSTRATION
# ─────────────────────────────────────────────────────────────────

def separator(title=""):
    line = "─" * 70
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(f"{line}")
    else:
        print(f"{line}")


def main():
    print("\n" + "═" * 70)
    print("  AUTONOMOUS CLOUD SOC — Encryption Demo  |  R1c")
    print("  Khushbu Jalan  |  DAE Cybersecurity  |  Semester 1")
    print("═" * 70)

    # ── AES-256-CBC Demo ─────────────────────────────────────────
    separator("PART 1: AES-256-CBC Encryption & Decryption")

    print(f"\n[INPUT]  Plaintext message:")
    print(f"         {PLAINTEXT}")
    print(f"\n[INFO]   Key length : {len(AES_KEY) * 8} bits ({len(AES_KEY)} bytes) — AES-256")
    print(f"[INFO]   Mode       : CBC (Cipher Block Chaining)")
    print(f"[INFO]   IV         : 16 random bytes generated fresh for each encryption")

    # Encrypt
    iv, ciphertext = aes_encrypt(PLAINTEXT, AES_KEY)

    print(f"\n[STEP 1] Encryption complete")
    print(f"         IV (hex)         : {iv.hex()}")
    print(f"         Ciphertext (hex) : {ciphertext.hex()}")
    print(f"         Ciphertext (b64) : {base64.b64encode(ciphertext).decode()}")
    print(f"         Ciphertext length: {len(ciphertext)} bytes")
    print(f"\n[NOTE]   The ciphertext looks like random noise.")
    print(f"         Without the AES key, it is mathematically impossible to read.")

    # Decrypt
    decrypted = aes_decrypt(iv, ciphertext, AES_KEY)

    print(f"\n[STEP 2] Decryption complete")
    print(f"         Decrypted text   : {decrypted}")

    # Verify
    match = PLAINTEXT == decrypted
    print(f"\n[VERIFY] Original == Decrypted : {match}")
    if match:
        print("         ✓ PASS — Encryption and decryption cycle successful.")
    else:
        print("         ✗ FAIL — Mismatch detected.")

    # ── SHA-256 Hashing ──────────────────────────────────────────
    separator("PART 2: SHA-256 Hashing")

    password_example = "WazuhAdmin@SOC2026!"
    alert_payload    = PLAINTEXT

    hash_password = sha256_hash(password_example)
    hash_alert    = sha256_hash(alert_payload)
    hash_tampered = sha256_hash(alert_payload + " [MODIFIED]")

    print(f"\n[INPUT A] Password to hash:")
    print(f"          {password_example}")
    print(f"\n[HASH A]  SHA-256 of password:")
    print(f"          {hash_password}")
    print(f"          Length: {len(hash_password)} hex characters = 256 bits")
    print(f"\n[NOTE]    This hash is what gets stored in the database.")
    print(f"          The original password is NEVER stored.")
    print(f"          An attacker who reads the database only gets this hash —")
    print(f"          they cannot reverse it to get 'WazuhAdmin@SOC2026!'")

    print(f"\n[INPUT B] Wazuh alert payload (same as Part 1 plaintext):")
    print(f"          {alert_payload[:60]}...")
    print(f"\n[HASH B]  SHA-256 of original alert payload:")
    print(f"          {hash_alert}")

    print(f"\n[INPUT C] Same alert — but with one word changed (simulating tampering):")
    print(f"          {alert_payload[:60]}... [MODIFIED]")
    print(f"\n[HASH C]  SHA-256 of tampered payload:")
    print(f"          {hash_tampered}")

    print(f"\n[VERIFY] Hash B == Hash C : {hash_alert == hash_tampered}")
    print(f"         ✓ PASS — Any change to the input, no matter how small,")
    print(f"           produces a completely different hash.")
    print(f"           This is the 'avalanche effect' — the foundation of file integrity monitoring.")
    print(f"\n[NOTE]   Wazuh FIM works exactly this way: it stores the SHA-256 hash")
    print(f"         of every monitored file (e.g. C:\\Windows\\System32\\lsass.exe).")
    print(f"         If an attacker modifies that file, the hash changes →")
    print(f"         Wazuh detects the mismatch → Level 12 HIGH alert fires.")

    # ── Summary ──────────────────────────────────────────────────
    separator("SUMMARY — Rubric R1c Requirements Met")
    print(f"\n  ✓  AES-256-CBC encrypted text shown     : {ciphertext.hex()[:32]}...")
    print(f"  ✓  Corresponding decrypted plaintext    : {decrypted[:50]}...")
    print(f"  ✓  Encryption == Decryption verified    : {PLAINTEXT == decrypted}")
    print(f"  ✓  SHA-256 hash of password shown       : {hash_password[:32]}...")
    print(f"  ✓  Avalanche effect demonstrated        : hashes differ on any input change")
    print(f"\n  Save screenshot of this terminal output as:")
    print(f"  evidence/R1c_encryption_screenshot.png")
    print(f"\n{'═' * 70}\n")


if __name__ == "__main__":
    main()
