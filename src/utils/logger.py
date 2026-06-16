import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_app_logger() -> logging.Logger:
    """
    Configures a lightweight event logger optimized for production environments.

    Returns:
        logging.Logger: Configured logger instance.
    """

    logger = logging.getLogger("FastPrint")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    base_dir = Path.cwd()
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "fastprint.log"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Global instance ready for import across the application
logger = setup_app_logger()
