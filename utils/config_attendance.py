import os
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment

# ===============================
# ENV TOGGLES
# ===============================
USE_SSH = os.getenv("USE_SSH", "false").lower() == "true"

# ===============================
# SSH CONFIG (ONLY IF USE_SSH=True)
# ===============================
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

# ===============================
# DATABASE CONFIG
# ===============================
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ===============================
# ATTENDANCE RULES
# ===============================
LATE_GRACE_MINUTES = int(os.getenv("LATE_GRACE_MINUTES", 10))
EARLY_LEAVE_GRACE_MINUTES = int(os.getenv("EARLY_LEAVE_GRACE_MINUTES", 10))

HALF_DAY_LATE_THRESHOLD = int(os.getenv("HALF_DAY_LATE_THRESHOLD", 120))
HALF_DAY_WORK_RATIO = float(os.getenv("HALF_DAY_WORK_RATIO", 0.5))
