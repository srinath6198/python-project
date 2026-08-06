from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a password with Argon2 before it is stored in the database."""
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a supplied password against its stored hash."""
    return password_hash.verify(plain_password, hashed_password)
