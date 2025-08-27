# Use the base image provided by AWS for Python Lambda functions
FROM public.ecr.aws/lambda/python:3.12

# Install git, necessary to clone the repository
RUN dnf install git -y

# Copy the Python script into the container
COPY script_lambda.py ./
COPY ccft_access.py ./

# Copy the entire project (including pyproject.toml)
COPY . .

# Install Python packages and resource-lister from local source
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install boto3 pexpect && \
    python3 -m pip install -e .

# Set environment variable for AWS Region
ENV AWS_DEFAULT_REGION=ca-central-1

# Set custom environment variables
ENV OUTPUT_PATH='/tmp'

# Set the CMD to use the Lambda handler
CMD ["script_lambda.lambda_handler"]