"""Centralized logging configuration for the DPR AI Simulator."""
import logging
import sys
from pathlib import Path

# Get project root (parent of src directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default log file location - logs/app.log in project root
DEFAULT_LOG_FILE = PROJECT_ROOT / 'logs' / 'app.log'


def setup_logger(name: str = "dpr_simulator", log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Setup centralized logging for the application.
    
    This sets up the root logger which all child loggers will inherit from.
    Child loggers like 'dpr_simulator.agents.absorb' will automatically use
    the handlers configured on the root logger.
    
    Args:
        name: Logger name (default: "dpr_simulator")
        log_file: Optional log file path. If None, uses DEFAULT_LOG_FILE.
                 Set to False to disable file logging.
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logger instance
    """
    # Get the root logger and all child loggers
    root_logger = logging.getLogger(name)
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler - output to terminal with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - save to logs/app.log with detailed format
    if log_file is not False:
        log_path = Path(log_file) if log_file else DEFAULT_LOG_FILE
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Don't propagate to parent (avoid duplicate messages)
    root_logger.propagate = False
    
    return root_logger


def get_logger(name: str = None) -> logging.Logger:
    """Get an existing logger or create a new one with default settings.
    
    Args:
        name: Logger name. If None, returns the root 'dpr_simulator' logger.
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"dpr_simulator.{name}")
    return logging.getLogger("dpr_simulator")


# Pre-configured loggers for key components
logger_simulator = get_logger("simulator")
logger_agents = get_logger("agents")
logger_members = get_logger("members")
logger_ui = get_logger("ui")
logger_models = get_logger("models")
