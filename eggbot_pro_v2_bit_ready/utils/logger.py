import os
from datetime import datetime

LOG_DIR = "logs"
BIT_LOG = os.path.join(LOG_DIR, "bit_log.txt")
ADMIN_LOG = os.path.join(LOG_DIR, "admin_actions.txt")
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg, category="bit"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_line = f"[{timestamp}] {msg}"
    print(full_line)

    log_file = BIT_LOG if category == "bit" else ADMIN_LOG
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(full_line + "\n")
