import importlib
import logging

logger = logging.getLogger()

logger.setLevel(logging.ERROR)

def process(process_config):
    """
    Main processing engine
    Calls implemenation function based on service configuration
    """
    print("Processing ....Please wait .... ")
    
    implclass = process_config.get("implclass")
    implfunction = process_config.get("implfunction")
    
    if not implclass or not implfunction:
        logger.error(f"Missing implclass or implfunction in process_config: {process_config}")
        raise ValueError("Missing implclass or implfunction")
    
    try:
        # Try the full import path first
        module_name = f"resource_lister.processor.{implclass}"
        logger.info(f"Attempting to import module: {module_name}")
        
        module = importlib.import_module(module_name)
        logger.info(f"Successfully imported module: {module}")
        
        # Get the function
        if hasattr(module, implfunction):
            func = getattr(module, implfunction)
            logger.info(f"Calling {implfunction} from {implclass}")
            func(process_config)
        else:
            logger.error(f"Function {implfunction} not found in module {implclass}")
            raise AttributeError(f"Function {implfunction} not found in module {implclass}")
            
    except ImportError as e:
        logger.error(f"Failed to import module {implclass}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in core processor: {e}")
        raise
