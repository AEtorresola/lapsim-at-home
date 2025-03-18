import logging
import os
from logging.handlers import RotatingFileHandler
import datetime

def setup_logger(log_name=None, log_dir='logs'):
    """Set up a logger with both console and file handlers.
    
    Args:
        log_name: Name for the log file. If None, uses script filename
        log_dir: Directory for log files (created if doesn't exist)
    
    Returns:
        A configured logger object
    """
    # If no log name provided, use the script filename
    if log_name is None:
        log_name = os.path.splitext(os.path.basename(__file__))[0]
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates when function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create log file path with date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{log_name}_{date_str}.log")
    
    # File handler (rotating to keep file size manageable)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Show INFO and above in console

    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(module)s | %(message)s'
    )
    # console_format = logging.Formatter(
    #     '%(asctime)s | %(levelname)-8s | %(message)s'
    # )
    console_handler.setFormatter(console_format)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

if __name__ == "__main__":
        
# Example usage
    logger = setup_logger()

# Now you can use logger throughout your script:
    logger.debug("Detailed debug information (file only)")
    logger.info("General information (file and console)")
    logger.warning("Warning message (file and console)")
    logger.error("Error message (file and console)")
    logger.critical("Critical failure (file and console)")

# Can also log exceptions with traceback
    try:
        x = 1 / 0
    except Exception as e:
        logger.exception("An error occurred")
