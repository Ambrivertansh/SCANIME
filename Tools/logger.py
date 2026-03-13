import logging
import sys
import os
from datetime import datetime, timedelta


class StyledFormatter(logging.Formatter):
    """Custom formatter with colors and icons."""

    FORMAT_BASE = "[%(asctime)s] 🛠️ [%(levelname)s] %(filename)s:%(lineno)d ➤ %(message)s"

    FORMATS = {
        logging.DEBUG: "\033[38;5;87m🔍 " + FORMAT_BASE + "\033[0m",       # Cyan
        logging.INFO: "\033[38;5;85mℹ️  " + FORMAT_BASE + "\033[0m",        # Sea Green
        logging.WARNING: "\033[38;5;227m⚠️  " + FORMAT_BASE + "\033[0m",    # Lemon Yellow
        logging.ERROR: "\033[38;5;209m❌ " + FORMAT_BASE + "\033[0m",       # Orange Red
        logging.CRITICAL: "\033[38;5;171m💀 " + FORMAT_BASE + "\033[0m",    # Electric Purple
    }

    def format(self, record):
        fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class FileHandler(logging.Handler):
    """File handler with 1-hour auto cleanup."""

    def __init__(self, filename="log.txt"):
        super().__init__()
        self.filename = filename
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(minutes=5)  # Clean every 5 minutes

        self.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        ))

    def _cleanup_old_logs(self):
        """Remove log entries older than 1 hour."""
        try:
            if not os.path.exists(self.filename):
                return

            cutoff_time = datetime.now() - timedelta(hours=1)

            with open(self.filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            recent_lines = []
            for line in lines:
                if line.startswith('['):
                    try:
                        timestamp_str = line[1:20]  # Extract [YYYY-MM-DD HH:MM:SS]
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if log_time >= cutoff_time:
                            recent_lines.append(line)
                    except ValueError:
                        recent_lines.append(line)
                else:
                    recent_lines.append(line)

            with open(self.filename, 'w', encoding='utf-8') as f:
                if recent_lines:
                    f.writelines(recent_lines)

        except Exception:
            pass  # Silent fail for cleanup errors

    def emit(self, record):
        """Write log with occasional cleanup."""
        try:
            if datetime.now() - self.last_cleanup >= self.cleanup_interval:
                self._cleanup_old_logs()
                self.last_cleanup = datetime.now()

            msg = self.format(record)
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')

        except Exception:
            pass  # Silent fail for write errors


def get_logger(name="app"):
    """Get configured logger with console and file output."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(StyledFormatter())
    logger.addHandler(console)

    # File handler with auto cleanup
    file_handler = FileHandler("log.txt")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    logger.propagate = False
    
    return logger

