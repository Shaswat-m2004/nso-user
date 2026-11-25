import os
import sys
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("USER_MANAGER_SECRET", "local-user-manager-secret")
    
    # Base directory logic handles both frozen (PyInstaller) and standard execution
    if getattr(sys, "frozen", False):
        BASE_DIR = Path(sys.executable).resolve().parent
    else:
        # Resolves to the root 'warehouse_manager' folder
        BASE_DIR = Path(__file__).resolve().parent.parent