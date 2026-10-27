"""
Configuration module — reads settings from environment variables.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR_BOOTSTRAP = Path(__file__).resolve().parent.parent
if str(BASE_DIR_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_BOOTSTRAP))

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DEMO_PROJECT_DIR = BASE_DIR / "demo_project"
REPORTS_DIR = BASE_DIR / "backend" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Gemini
# ─────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ─────────────────────────────────────────────
# Demo / Fallback Mode
# ─────────────────────────────────────────────
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

# If no API key, automatically enable demo mode
if not GEMINI_API_KEY:
    DEMO_MODE = True

# ─────────────────────────────────────────────
# App Settings
# ─────────────────────────────────────────────
APP_TITLE = "AI QA Engineer"
APP_VERSION = "1.0.0"
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1")

# ─────────────────────────────────────────────
# Timeouts & Limits
# ─────────────────────────────────────────────
ANALYSIS_TIMEOUT: int = int(os.getenv("ANALYSIS_TIMEOUT", "300"))  # 5 minutes
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILES: int = int(os.getenv("MAX_FILES", "50"))
