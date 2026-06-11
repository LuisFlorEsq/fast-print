import logging
import os

def setup_app_logger() -> logging.Logger:
    """
    Configures a lightweight event logger optimized for production environments.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    log_file = "fastprint_error.log"
    logger = logging.getLogger("FastPrint")
    logger.setLevel(logging.ERROR)

    # Prevent duplicating handlers if the module is reloaded dynamically
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Global instance ready for import across the application
logger = setup_app_logger()