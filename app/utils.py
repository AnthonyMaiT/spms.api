from passlib.context import CryptContext

# for hashing passwords using the bcrypt method
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# hashes a plain text password
def hash(password: str):
    return pwd_context.hash(password)

# verifies a plain text password is the same as the hashed password
def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)