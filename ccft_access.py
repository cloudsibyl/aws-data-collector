# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This resembles the access to AWS Customer Carbon Footprint Tool data
# from the AWS Billing Console. Hence it is not using an official AWS interface and
# might change at any time without notice and just stop working.

import boto3
import requests
import argparse
import json
from urllib.parse import urlencode
from datetime import datetime
import sys
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os

def extract_emissions_data(startDate, endDate, credentials):
    billing_region = 'us-east-1'

    if credentials.token is None:
        # this is most likely an IAM or root user
        exit("You seem to run this with an IAM user. Assume an account's role instead.")

    #get the account ID to include it in the response
    sts_client = boto3.client(
         'sts',
         aws_access_key_id=credentials.access_key,
         aws_secret_access_key=credentials.secret_key,
         aws_session_token=credentials.token
    )

    accountID = sts_client.get_caller_identity()["Account"]

    # Create a new session in which all cookies are set during login
    s = requests.Session()

    aws_federated_signin_endpoint = 'https://signin.aws.amazon.com/federation'

    # Get SigninToken
    signin_token_params = {
        "Action": "getSigninToken",
        "Session": {
            "sessionId": credentials.access_key,
            "sessionKey": credentials.secret_key,
            "sessionToken": credentials.token
        }
    }
    signin_token_url = "%s?%s" % (
        aws_federated_signin_endpoint, urlencode(signin_token_params))
    signin_token_request = s.get(signin_token_url)
    signin_token = json.loads(signin_token_request.text)['SigninToken']

    # Create Login URL
    login_params = {
        "Action": "login",
        "Destination": "https://console.aws.amazon.com/",
        "SigninToken": signin_token
    }
    login_url = "%s?%s" % (aws_federated_signin_endpoint, urlencode(login_params))

    r = s.get(login_url)
    r.raise_for_status()

    # grap the xsrf token once
    r = s.get("https://console.aws.amazon.com/billing/home?state=hashArgs")
    r.raise_for_status()
    xsrf_token = r.headers["x-awsbc-xsrf-token"]

    # call the proxy via POST
    cft_request = {
        "headers": {
            "Content-Type": "application/json"
        },
        "path": "/get-carbon-footprint-summary",
        "method": "GET",
        "region": billing_region,
        "params": {
            "startDate": startDate,
            "endDate": endDate
        }
    }
    cft_headers = {
        "x-awsbc-xsrf-token": xsrf_token
    }

    try:
        r = s.post(
            "https://%s.console.aws.amazon.com/billing/rest/api-proxy/carbonfootprint" % (billing_region),
            data=json.dumps(cft_request),
            headers=cft_headers
        )
        r.raise_for_status()
        emissions = r.json()

        emissions_data = {
            "accountId": accountID,
            "query": {
                "queryDate": datetime.today().strftime("%Y-%m-%d"),
                "startDate": startDate,
                "endDate": endDate,
            },
            "emissions": emissions
        }
        return emissions_data

    except Exception as e:
            if str(e) == "404 Client Error: Not Found for url: https://us-east-1.console.aws.amazon.com/billing/rest/api-proxy/carbonfootprint":
                raise Exception("No carbon footprint report is available for this account at this time:", accountID, "If no report is available, your account might be too new to show data. There is a delay of three months between the end of a month and when emissions data is available.")
            else:
                raise Exception("An error occured: " + str(e))

def convert_json_to_csv(data, account_id):
    """
    Converts JSON data to a list of comma-separated strings (CSV format).
    
    Parameters:
    - json_data (str): JSON string containing account details and emissions entries.
    
    Returns:
    - List[str]: A list of strings where each string is a comma-separated row of the CSV.
    """
    creation_date = datetime.now().strftime("%Y-%m-%d")
    service_name = "Cost"
    function_name = "carbon_footprint"

    # Update each emission entry with additional fields
    for item in data:
        item.update({
            "Account": account_id,
            "Creation_Date": creation_date,
            "service_name": service_name,
            "function_name": function_name
        })

    # Headers considering all keys might not be present in all records
    unique_keys = set(key for entry in data for key in entry.keys())
    headers = ["Account", "Creation_Date", "service_name", "function_name"] + sorted(unique_keys - {"Account", "Creation_Date", "service_name", "function_name"})

    # Prepare CSV data
    csv_data = [headers]  # first row is the headers
    for entry in data:
        csv_data.append([entry.get(key, '') for key in headers])

    # Convert list of lists to list of comma-separated strings
    csv_strings = [",".join(map(str, row)) for row in csv_data]
    return csv_strings

def get_output_path():
    """
    Return the path to the /tmp directory where Lambda is allowed to write files.
    :return: /tmp as the output path
    """
    dir_path = os.getenv("OUTPUT_PATH")
    return dir_path

def get_file_path(service_name, function_name, dir_path, file_type):
    """
     Generate file path based on service_name and function_name
    :param service_name like s3, lambda
    :param function_name like list_buckets
    :return: None
    """
    # if not os.path.exists(dir_path):
    #     ValueError("Invalid Path to store the file  {}".format(dir_path))
    dir_path = get_output_path()
    current_date = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    file_name = "{}_{}_{}.{}".format(
        service_name, function_name, current_date, file_type)
    output_path = os.path.join(dir_path, "output")
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    file_path = os.path.join(output_path, file_name)
    return file_path

def save_csv(csv_data, service_name, function_name, dir_path):
    """
     save file as .csv
    :param csv_data data in list of comma seperated strings
    :param service_name like s3, lambda
    :param function_name like list_buckets
    :return: None
    """
    file_full_path = None
    if len(csv_data) > 0:
        file_full_path = get_file_path(
            service_name, function_name, dir_path, "csv")
        f = open(file_full_path, "w")
        for row in csv_data:
            f.write(row + "\n")
        print("RESULT : File is generated at location {} ".format(file_full_path))
    else:
        print("RESULT : No records . ")
    return file_full_path

def save_json(json_data, service_name, function_name, dir_path):
    """
    Save data as a .json file.
    :param json_data: data to be saved in JSON format
    :param service_name: like s3, lambda
    :param function_name: like list_buckets
    :param dir_path: directory path where the file will be saved
    :return: None
    """
    file_full_path = None
    if json_data:
        file_full_path = get_file_path(service_name, function_name, dir_path, "json")
        with open(file_full_path, "w") as json_file:
            json.dump(json_data, json_file, indent=4)
        print("RESULT : File is generated at location {} ".format(file_full_path))
    else:
        print("RESULT : No records.")
    return file_full_path

class S3Uploader():
    def upload_file(self, file_full_path):
        # Get full file path
        partition = "misc"
        if file_full_path:
            datetime_object = datetime.now().strftime("%Y-%m-%d")
            path_list = file_full_path.split(os.path.sep)
            file_name = path_list[(len(path_list)-1)]
            partition = "misc"
            s3key = "data/{}/date={}/{}".format(partition,
                                                datetime_object, file_name)
            try:
                s3_bucket = os.getenv("s3_bucket")
                _session = boto3.Session()
                s3_client = _session.client('s3')
                s3_client.upload_file(file_full_path, s3_bucket, s3key)
                print("S3: File is loaded--> {}/{}".format(s3_bucket, s3key))
                self.clean_up(file_full_path)
            except Exception as e:
                if str(e)!="An error occurred (InvalidAccessKeyId) when calling the ListBuckets operation: The AWS Access Key Id you provided does not exist in our records.":
                    print("Error in uploading file to s3")
                    print(e)

    def clean_up(self, file_full_path):
        print("Removing file {}".format(file_full_path))
        if os.path.exists(file_full_path):
            os.remove(file_full_path)

if __name__ == "__main__":
    description = """
    Script to extract carbon emissions from the AWS Customer Carbon Footprint Tool.
    The data is queried for the current month.
    """
    # Calculate start and end dates for the current month
    
    # current_date = datetime.now()
    # start_date = datetime(current_date.year, current_date.month, 1)
    # end_date = start_date + relativedelta(months=1, days=-1)
    
     # calculate three months past (when new carbon emissions data is available)
    three_months = date.today() - relativedelta(months=3)
    # get the date with 1st day of the month
    year = three_months.year
    month = three_months.month
    first_date = datetime(year, month, 1)
    
    # The default end date is the first date of the month three months ago, and the default start date is 36 months before
    default_end_date=first_date.strftime("%Y-%m-%d")
    default_start_date=(first_date - relativedelta(months=36)).strftime("%Y-%m-%d")

    session = boto3.Session()
    credentials = session.get_credentials()

    try:
        emissions_data = extract_emissions_data(default_start_date, default_end_date, credentials)
        # modify temperory to save the file
        data = json.dumps(emissions_data)
        data = json.loads(data)
        account_id = data['accountId']
        s3_uploader = S3Uploader()
        for key, entry in data['emissions'].items():
            csv_data = convert_json_to_csv(entry, account_id)
            dir_path = get_output_path()
            file_full_path = save_csv(csv_data, "cost", "carbon_footprint_{}".format(key), dir_path)
            s3_uploader.upload_file(file_full_path)
        json_data_file_full_path = save_json(emissions_data, "cost", "carbon_footprint", dir_path)
        s3_uploader.upload_file(json_data_file_full_path)
    except Exception as e:
         sys.stderr.write(str(e))
         sys.exit(1)
