from .menu import menu_processor
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main():
    args = menu_processor.setup_args()
    menu_processor.process(args)

if __name__ == "__main__":
    main()