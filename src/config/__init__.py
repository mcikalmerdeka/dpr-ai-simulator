"""Configuration module for DPR AI Simulator."""

from .settings import settings
from .logging_config import setup_logger

__all__ = [
    "settings",
    "setup_logger",
]
