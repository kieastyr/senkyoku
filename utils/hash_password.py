import bcrypt
import getpass
import sys

def generate_hash():
    """Generates a bcrypt hash for a password entered by the user."""
    print("--- Streamlit Password Hasher ---")
    password = getpass.getpass("Enter the password to hash: ")
    if not password:
        print("Error: Password cannot be empty.")
        sys.exit(1)
        
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)
        
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    
    print("\n[Success] Your password hash is:")
    print(hashed.decode())
    print("\nCopy the hash above into your .streamlit/secrets.toml file.")

if __name__ == "__main__":
    try:
        generate_hash()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
