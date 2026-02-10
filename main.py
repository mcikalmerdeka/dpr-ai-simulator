"""DPR AI Simulator - Main entry point."""

from src.ui import launch_app
from src.config import setup_logger


def main():
    """Launch the DPR AI Simulator application."""
    # Initialize logging at app startup
    logger = setup_logger("dpr_simulator")
    
    logger.info("=" * 50)
    logger.info("🏛️ Starting DPR AI Simulator...")
    logger.info("Simulasi AI untuk Menyerap, Menghimpun, dan")
    logger.info("Menindaklanjuti Aspirasi Rakyat Indonesia")
    logger.info("=" * 50)
    
    launch_app()


if __name__ == "__main__":
    main()
