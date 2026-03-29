import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

class Config:
    # Priority: Env Var > Railway Volume (/data) > Local File
    if os.getenv('DATABASE_PATH'):
        DATABASE_PATH = os.getenv('DATABASE_PATH')
    elif os.path.exists('/data') and os.access('/data', os.W_OK):
        DATABASE_PATH = '/data/agent.db'
    else:
        # Fallback to current directory, ensuring it's writable
        DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'agent.db')
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Print for debugging in Railway logs
    print(f"[*] Initializing database at: {DATABASE_PATH}")
    
    DATABASE_URI = DATABASE_PATH
    UPLOADS_DIR = os.getenv('UPLOADS_DIR', os.path.join(os.path.dirname(__file__), 'uploads'))
    
    # Secret Key for Flask sessions
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Fernet encryption key for sensitive data
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Initialize keys if they don't exist
def initialize_keys():
    # Only perform auto-init if we aren't in a production environment (no keys set)
    if os.getenv('SECRET_KEY') and os.getenv('ENCRYPTION_KEY'):
        return

    env_file = os.path.join(os.path.dirname(__file__), '.env')
    dirty = False
    
    if not Config.SECRET_KEY:
        Config.SECRET_KEY = os.urandom(24).hex()
        dirty = True
        
    if not Config.ENCRYPTION_KEY:
        Config.ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
        dirty = True
        
    if dirty:
        # Check if we can write to .env
        try:
            with open(env_file, 'a') as f:
                if not os.getenv('SECRET_KEY'):
                    f.write(f"SECRET_KEY={Config.SECRET_KEY}\n")
                if not os.getenv('ENCRYPTION_KEY'):
                    f.write(f"ENCRYPTION_KEY={Config.ENCRYPTION_KEY}\n")
            # Reload to ensure OS env has it
            load_dotenv()
        except IOError:
            # If in a read-only filesystem or restricted environment, just log it
            print("Warning: Could not write to .env. Keys will not persist across restarts unless set in environment.")

# Run initialization
initialize_keys()

def get_fernet():
    return Fernet(Config.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_value(value: str) -> str:
    if not value: return value
    f = get_fernet()
    return f.encrypt(value.encode('utf-8')).decode('utf-8')

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value: return encrypted_value
    f = get_fernet()
    return f.decrypt(encrypted_value.encode('utf-8')).decode('utf-8')
