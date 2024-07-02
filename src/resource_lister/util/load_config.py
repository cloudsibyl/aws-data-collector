import os
import json
import logging

# Set up our logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def load_account_config():
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        relative_path_to_config = os.path.join('..', 'session_mgr', 'account_config.json')
        file_path = os.path.abspath(os.path.join(dir_path, relative_path_to_config))
        f = open(file_path)
        master_account_json = json.load(f)
        account_id = str(os.getenv("account_id"))
        master_account_json["master_account"]["account_id"] = account_id
        master_account_json["master_account"]["account_config_type"] = '1'
    except KeyError as err:
            logger.error(
                "Please check account_config.json file path or env variables is not set correctly.")
            raise err
    return master_account_json


def load_config_attributes_json():
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        relative_path_to_config = os.path.join('..', 'config_mgr', 'config.json')
        file_path = os.path.abspath(os.path.join(dir_path, relative_path_to_config))
        f = open(file_path)
        config_json = json.load(f)
        config_json["format_type"] = 'csv'
        config_json["output_to"] = 's3'
        config_json["required"] = 'no'
        config_json["account_split"] = 'no'
        config_json["s3_bucket"] = str(os.getenv("s3_bucket"))
    except KeyError as err:
            logger.error(
                "Please check config.json file path or env variables is not set correctly.")
            raise err
    return config_json