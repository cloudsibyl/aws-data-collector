import resource_lister.menu.menu_processor as menu_processor
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main():
    args = menu_processor.setup_args()
    menu_processor.process(args)

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        logger.info(f"Lambda event: {json.dumps(event)}")
        
        # Process the event (you can customize this based on your needs)
        if 'servicename' in event and 'functionname' in event:
            # Handle specific service/function calls
            args = menu_processor.setup_args()
            # You can modify args here based on the event
            menu_processor.process(args)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Data collection completed successfully',
                    'event': event
                })
            }
        else:
            # Default processing
            main()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Default processing completed successfully'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

if __name__ == "__main__":
    main()