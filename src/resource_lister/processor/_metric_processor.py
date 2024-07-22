import botocore
import concurrent.futures
from botocore.config import Config
from resource_lister.boto_formatter.service_formatter import service_response_formatter
from resource_lister.util.session_util import SessionHandler
from resource_lister.util.s3_util import S3Uploader
import logging
import datetime
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger()

def process(process_config):
    accounts = process_config["accounts"]
    regions = process_config["regions"]
    service_name = process_config["service_name"]
    function_name = process_config["function_name"]
    attributes = process_config["attributes"]
    attributes["pagination"] = "True"
    metric_parameters = process_config.get("metric_parameters", {})
    pagination_attributes = None
    current_date = datetime.datetime.now().strftime("%m/%d/%Y")
    if "pagination_attributes" in process_config.keys():
        pagination_attributes = process_config["pagination_attributes"]

    object_list = []
    if metric_parameters["Namespace"] == "AWS/EC2":
        intances = get_instance_ids(accounts, regions)
        dimension_name = "InstanceId"
    elif metric_parameters["Namespace"] == "AWS/EBS":
        intances = get_volume_ids(accounts, regions)
        dimension_name = "VolumeId"
    elif metric_parameters["Namespace"] == "AWS/ECS":
        intances = get_cluster_names(accounts, regions)
        dimension_name = "ClusterName"
    else:
        raise Exception("Namespace not supported")

    if intances:
        object_list = []
        for intance in intances:
            metric_parameters["MetricName"] = function_name
            metric_parameters["Dimensions"] = [{"Name": dimension_name, "Value": intance}]
            object_list.extend(process_metrics(accounts, regions, service_name, function_name, intance, metric_parameters, current_date))
        process_result(process_config, service_response_formatter(service_name, function_name, object_list, attributes))

def get_instance_ids(accounts, regions):
    instance_ids = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for account in accounts:
            for region in regions:
                futures.append(executor.submit(fetch_instance_ids, SessionHandler.get_new_session(account), region))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                instance_ids.extend(result)
                if len(instance_ids) >= 60:
                    return instance_ids[:60]
            except Exception as exc:
                logger.error(exc)
    return instance_ids[:60]

def fetch_instance_ids(session, region):
    ec2_client = session.client("ec2", config=Config(region_name=region))
    paginator = ec2_client.get_paginator("describe_instances")
    instance_ids = []
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                instance_ids.append(instance["InstanceId"])
                if len(instance_ids) >= 60:
                    return instance_ids
    return instance_ids

def get_cluster_names(accounts, regions):
    cluster_names = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for account in accounts:
            for region in regions:
                futures.append(executor.submit(fetch_cluster_names, SessionHandler.get_new_session(account), region))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                cluster_names.extend(result)
                if len(cluster_names) >= 60:
                    return cluster_names[:60]
            except Exception as exc:
                logger.error(exc)
    return cluster_names[:60]

def fetch_cluster_names(session, region):
    ecs_client = session.client("ecs", config=Config(region_name=region))
    paginator = ecs_client.get_paginator('list_clusters')
    cluster_names = []

    for page in paginator.paginate():
        cluster_arns = page.get('clusterArns', [])
        
        for cluster_arn in cluster_arns:
            # Describe the cluster to get its name
            cluster_info = ecs_client.describe_clusters(clusters=[cluster_arn])
            cluster = cluster_info['clusters'][0]
            cluster_name = cluster['clusterName']
            cluster_names.append(cluster_name)
            if len(cluster_names) >= 60:
                return cluster_names
    
    return cluster_names

def get_volume_ids(accounts, regions):
    volume_ids = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for account in accounts:
            for region in regions:
                # Assume SessionHandler.get_new_session handles creating sessions with appropriate credentials
                futures.append(executor.submit(fetch_volume_ids, SessionHandler.get_new_session(account), region))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                volume_ids.extend(result)
                if len(volume_ids) >= 60:
                    return volume_ids[:60]
            except Exception as exc:
                logger.error(exc)
    return volume_ids[:60]

def fetch_volume_ids(session, region):
    ec2_client = session.client("ec2", config=Config(region_name=region))
    paginator = ec2_client.get_paginator("describe_volumes")
    volume_ids = []
    for page in paginator.paginate():
        for volume in page['Volumes']:
            volume_ids.append(volume['VolumeId'])
            if len(volume_ids) >= 60:
                return volume_ids
    return volume_ids

def process_metrics(accounts, regions, service_name, function_name, intance, metric_parameters, current_date):
    metrics_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for account in accounts:
            for region in regions:
                futures.append(executor.submit(fetch_metrics, SessionHandler.get_new_session(account), region, account, service_name, function_name, intance, metric_parameters, current_date))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                metrics_results.append(result)
            except Exception as exc:
                logger.error(exc)
    return metrics_results

def fetch_metrics(session, region, account, service_name, function_name, intance, metric_parameters, current_date):
    prefix_columns = dict()
    prefix_columns["Account"] = account
    prefix_columns["Region"] = region
    prefix_columns["Creation_Date"] = current_date
    prefix_columns["service_name"] = service_name
    prefix_columns["function_name"] = function_name
    prefix_columns["instance_id"] = intance

    result = dict()
    object_list = []
    cw_client = session.client("cloudwatch", config=Config(region_name=region))
    response = cw_client.get_metric_statistics(
        Namespace=metric_parameters["Namespace"],
        MetricName=metric_parameters["MetricName"],
        Dimensions=metric_parameters["Dimensions"],
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=24),
        EndTime=datetime.datetime.utcnow(),
        Period=metric_parameters["Period"],
        Statistics=metric_parameters["Statistics"]
    )
    result['prefix_columns'] = prefix_columns
    result['result'] = [{'Datapoints': response['Datapoints']}]
    return result

def process_result(process_config, result):
    attributes = process_config["attributes"]
    # boto_formatter understand only file or print
    if attributes["output_to"] == "s3":
        S3Uploader().upload_file(dict(process_config), result)
    return result
