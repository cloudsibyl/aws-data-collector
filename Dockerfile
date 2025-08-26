# Use AWS Lambda Python 3.12 runtime as base (long-term supported)
FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR /var/task

# Set environment variables - FIX: Set PYTHONPATH to include src directory
ENV PYTHONPATH=/var/task/src
ENV AWS_DEFAULT_REGION=ca-central-1
ENV OUTPUT_PATH=/tmp

# Install system dependencies
RUN dnf install git -y

# Copy requirements file (if it exists)
COPY requirements.txt ./

# Install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy source code - FIX: Copy to the correct location
COPY src/ /var/task/src/

# Copy any additional Python files that might be needed
COPY *.py ./

# Set the CMD to your lambda handler
CMD ["src.resource_lister.main.lambda_handler"]