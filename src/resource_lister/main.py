from .menu import menu_processor
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
        
        # Check if this is a metrics collection event
        if 'service' in event:
            service_name = event['service']
            logger.info(f"Processing metrics collection for service: {service_name}")
            
            # Import the metric processor
            from .processor._metric_processor import process
            
            # Set up the process config for metrics collection
            import os
            
            # Debug logging for environment variables
            account_id = os.environ.get('account_id', 'default')
            s3_bucket = os.environ.get('s3_bucket', 'default-bucket')
            logger.info(f"Environment variables - account_id: {account_id}, s3_bucket: {s3_bucket}")
            
            # Determine the correct service_name based on the metric type
            if service_name.startswith('rds_'):
                actual_service_name = "cloudwatch"  # RDS metrics are in cloudwatch.json
            else:
                actual_service_name = service_name  # Keep original for other services
            
            process_config = {
                "accounts": [account_id],
                "regions": ["ca-central-1"],  # You can make this configurable
                "service_name": actual_service_name,  # Use 'cloudwatch' for RDS metrics
                "function_name": service_name,  # Keep the original metric name as function_name
                "attributes": {
                    "output_to": "s3",
                    "s3_bucket": s3_bucket
                }
            }
            
            logger.info(f"Process config created: {process_config}")
            
            # Process the metrics
            result = process(process_config)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Metrics collection completed for {service_name}',
                    'result': result
                })
            }
        else:
            # Default processing for other types of events
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