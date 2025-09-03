import json
import subprocess
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

def execute_resource_lister(config):
    logger.info(f"execute_resource_lister called with config: {config}")
    
    command = [
        "resource_lister",
        "--service", config['service'],
        "--option", str(config['option']),
        "--accounts", config['accounts'],
        "--regions", config['regions'],
        "--output", config['output']
    ]
    
    logger.info(f"Executing command: {command}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Command executed successfully. stdout length: {len(result.stdout)}")
        logger.info(f"stdout preview: {result.stdout[:200]}...")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute resource_lister for {config['service']}: {e}")
        logger.error(f"Error output: {e.stderr}")
        logger.error(f"Return code: {e.returncode}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in execute_resource_lister: {e}")
        return None

def execute_ccft_access():
    logger.info("execute_ccft_access called")
    try:
        command = ["python", "ccft_access.py"]
        logger.info(f"Executing ccft command: {command}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"ccft command executed successfully. stdout length: {len(result.stdout)}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute ccft_access.py in Docker: {e}")
        logger.error(f"Error output: {e.stderr}")
        return "Failed to execute ccft_access.py"
    except Exception as e:
        logger.error(f"Unexpected error in execute_ccft_access: {e}")
        return "Failed to execute ccft_access.py"

def generate_commands(service, option='1'):
    config = {
        "service": service,
        "option": option,
        "accounts": "all",
        "regions": "all",
        "output": "s3"
    }
    logger.info(f"generate_commands called with service={service}, option={option}, returning: {config}")
    return config

def lambda_handler(event, context):
    logger.info(f"lambda_handler called with event: {event}")
    logger.info(f"context: {context}")
    
    services = ['s3', 'ec2', 'ecs', 'cloudformation', 'cloudfront', 
                'cloudtrail', 'cloudwatch', 'codecommit', 'dynamodb', 'efs', 'eks', 'elbv2', 
                'emr', 'emr-serverless', 'lambda', 'rds', 'redshift', 
                'sagemaker', 'sns', 'sqs', 'ssm', 'organizations', 'CPUUtilization', 'mem_used_percent',
                'network_in', 'network_out', 'network_packets_in', 'network_packets_out', 'VolumeIOPS', 'VolumeThroughput', 'carbon_footprint', 
                'CPUReservation', 'MemoryReservation', 'rds_read_throughput', 'rds_write_throughput',
                'rds_replica_lag', 'rds_aurora_capacity_units', 'rds_cpu_utilization', 
                'rds_freeable_memory', 'rds_database_connections', 'rds_free_storage_space',
                'rds_read_iops', 'rds_write_iops']
    
    logger.info(f"Supported services: {services}")
    
    # Extract the service name from the event
    service = event.get('service')
    logger.info(f"Extracted service from event: {service}")
    
    if not service:
        logger.error("No service name provided in event")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Service name is required in the event payload"})
        }
    
    if service not in services:
        logger.error(f"Service {service} is not in supported services list")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Service {service} is not supported"})
        }
    
    logger.info(f"Service {service} is supported, proceeding with processing")
    
    results = {}
    
    if service == 'ec2':
        logger.info("Processing EC2 service")
        for i in range(1, 16):
            logger.info(f"Processing EC2 option {i}")
            result = execute_resource_lister(generate_commands(service, str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
        
        logger.info("Executing ccft_access for carbon footprint")
        result = execute_ccft_access()
        results['carbon_footprint'] = result if result else "Failed to execute"
        
    elif service in ['cloudfront', 'cloudwatch', 'lambda', 'sns']:
        logger.info(f"Processing {service} service (options 1-2)")
        for i in range(1, 3):
            logger.info(f"Processing {service} option {i}")
            result = execute_resource_lister(generate_commands(service, str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
    elif service == 'eks':
        logger.info("Processing EKS service (option 2)")
        result = execute_resource_lister(generate_commands(service, '2'))
        results[f'{service}_2'] = result if result else "Failed to execute"
    elif service == 'emr':
        logger.info("Processing EMR service (options 1-3)")
        for i in range(1, 4):
            logger.info(f"Processing EMR option {i}")
            result = execute_resource_lister(generate_commands(service, str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
    elif service in ['rds', 'sagemaker']:
        logger.info(f"Processing {service} service (options 1-5)")
        for i in range(1, 6):
            logger.info(f"Processing {service} option {i}")
            result = execute_resource_lister(generate_commands(service, str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
    elif service == 'CPUUtilization':
        logger.info("Processing CPUUtilization service (cloudwatch option 3)")
        result = execute_resource_lister(generate_commands('cloudwatch', '3'))
        results[service] = result if result else "Failed to execute"
    elif service == 'mem_used_percent':
        logger.info("Processing mem_used_percent service (cloudwatch option 4)")
        result = execute_resource_lister(generate_commands('cloudwatch', '4'))
        results[service] = result if result else "Failed to execute"
    elif service == 'network_in':
        logger.info("Processing network_in service (cloudwatch option 5)")
        result = execute_resource_lister(generate_commands('cloudwatch', '5'))
        results[service] = result if result else "Failed to execute"
    elif service == 'network_out':
        logger.info("Processing network_out service (cloudwatch option 6)")
        result = execute_resource_lister(generate_commands('cloudwatch', '6'))
        results[service] = result if result else "Failed to execute"
    elif service == 'network_packets_in':
        logger.info("Processing network_packets_in service (cloudwatch option 7)")
        result = execute_resource_lister(generate_commands('cloudwatch', '7'))
        results[service] = result if result else "Failed to execute"
    elif service == 'network_packets_out':
        logger.info("Processing network_packets_out service (cloudwatch option 8)")
        result = execute_resource_lister(generate_commands('cloudwatch', '8'))
        results[service] = result if result else "Failed to execute"
    elif service == 'VolumeIOPS':
        logger.info("Processing VolumeIOPS service (cloudwatch options 9-10)")
        for i in range(9, 11):
            logger.info(f"Processing VolumeIOPS option {i}")
            result = execute_resource_lister(generate_commands('cloudwatch', str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
    elif service == 'VolumeThroughput':
        logger.info("Processing VolumeThroughput service (cloudwatch options 11-12)")
        for i in range(11, 13):
            logger.info(f"Processing VolumeThroughput option {i}")
            result = execute_resource_lister(generate_commands('cloudwatch', str(i)))
            results[f'{service}_{i}'] = result if result else "Failed to execute"
    elif service == 'carbon_footprint':
        logger.info("Processing carbon_footprint service")
        result = execute_ccft_access()
        results[service] = result if result else "Failed to execute"
    elif service == 'CPUReservation':
        logger.info("Processing CPUReservation service (cloudwatch option 13)")
        result = execute_resource_lister(generate_commands('cloudwatch', '13'))
        results[service] = result if result else "Failed to execute"
    elif service == 'MemoryReservation':
        logger.info("Processing MemoryReservation service (cloudwatch option 14)")
        result = execute_resource_lister(generate_commands('cloudwatch', '14'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_read_throughput':
        logger.info("Processing rds_read_throughput service (cloudwatch option 21)")
        result = execute_resource_lister(generate_commands('cloudwatch', '21'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_write_throughput':
        logger.info("Processing rds_write_throughput service (cloudwatch option 22)")
        result = execute_resource_lister(generate_commands('cloudwatch', '22'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_replica_lag':
        logger.info("Processing rds_replica_lag service (cloudwatch option 23)")
        result = execute_resource_lister(generate_commands('cloudwatch', '23'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_aurora_capacity_units':
        logger.info("Processing rds_aurora_capacity_units service (cloudwatch option 24)")
        result = execute_resource_lister(generate_commands('cloudwatch', '24'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_cpu_utilization':
        config = generate_commands('cloudwatch', '15')
        result = execute_resource_lister(config)
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_freeable_memory':
        logger.info("Processing rds_freeable_memory service (cloudwatch option 17)")
        result = execute_resource_lister(generate_commands('cloudwatch', '17'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_database_connections':
        logger.info("Processing rds_database_connections service (cloudwatch option 16)")
        result = execute_resource_lister(generate_commands('cloudwatch', '16'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_free_storage_space':
        logger.info("Processing rds_free_storage_space service (cloudwatch option 18)")
        result = execute_resource_lister(generate_commands('cloudwatch', '18'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_read_iops':
        logger.info("Processing rds_read_iops service (cloudwatch option 19)")
        result = execute_resource_lister(generate_commands('cloudwatch', '19'))
        results[service] = result if result else "Failed to execute"
    elif service == 'rds_write_iops':
        logger.info("Processing rds_write_iops service (cloudwatch option 20)")
        result = execute_resource_lister(generate_commands('cloudwatch', '20'))
        results[service] = result if result else "Failed to execute"
    else:
        logger.info(f"Processing {service} service with default option 1")
        result = execute_resource_lister(generate_commands(service))
        results[service] = result if result else "Failed to execute"
    
    logger.info(f"Final results: {list(results.keys())}")
    logger.info(f"Results summary: {len([r for r in results.values() if r != 'Failed to execute'])} successful, {len([r for r in results.values() if r == 'Failed to execute'])} failed")
    
    # Log detailed results for debugging
    for service_name, result in results.items():
        if result == "Failed to execute":
            logger.error(f"Service {service_name} failed to execute")
        else:
            logger.info(f"Service {service_name} completed successfully with output length: {len(result) if result else 0}")
            if result and len(result) < 3000 and "DISCLAIMER" in result:
                logger.warning(f"Service {service_name} output appears to be mostly disclaimer text")
    
    return {
        "statusCode": 200 if all(results.values()) else 400,
        "body": json.dumps(results)
    }