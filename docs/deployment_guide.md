# AWS Data Collector Deployment Guide

This document outlines the steps to deploy the CloudSibyl AWS Data Collector function to different AWS regions using ECR.

## Prerequisites

- Docker installed and running
- AWS CLI configured with appropriate credentials
- Docker image `cloudsibyl-aws-data-collector:test` built locally

## Step 0: Test

```bash

docker build -t cloudsibyl-aws-data-collector:test .

# Login to ECR in ca-central-1
aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 767397677341.dkr.ecr.ca-central-1.amazonaws.com

# Tag the image for ca-central-1
docker tag cloudsibyl-aws-data-collector:test 767397677341.dkr.ecr.ca-central-1.amazonaws.com/cloudsibyl-aws-data-collector:test

# Push the image to ca-central-1
docker push 767397677341.dkr.ecr.ca-central-1.amazonaws.com/cloudsibyl-aws-data-collector:test
```

## Step 1: Set AWS Profile

Before deploying, ensure you're using the correct AWS profile:

```bash
# Set the default AWS profile to 'prod'
export AWS_DEFAULT_PROFILE=prod
export AWS_PROFILE=prod

# Verify the profile is set
aws sts get-caller-identity

docker build -t cloudsibyl-aws-data-collector:latest .
```

## Step 2: Deploy to Different Regions

### Canada Central (ca-central-1)

```bash
# Login to ECR in ca-central-1
aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 767397677341.dkr.ecr.ca-central-1.amazonaws.com

# Tag the image for ca-central-1
docker tag cloudsibyl-aws-data-collector:latest 767397677341.dkr.ecr.ca-central-1.amazonaws.com/cloudsibyl-aws-data-collector:latest

# Push the image to ca-central-1
docker push 767397677341.dkr.ecr.ca-central-1.amazonaws.com/cloudsibyl-aws-data-collector:latest
```

### US East (Ohio) - us-east-2

```bash
# Login to ECR in us-east-2
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 767397677341.dkr.ecr.us-east-2.amazonaws.com

# Tag the image for us-east-2
docker tag cloudsibyl-aws-data-collector:latest 767397677341.dkr.ecr.us-east-2.amazonaws.com/cloudsibyl-aws-data-collector:latest

# Push the image to us-east-2
docker push 767397677341.dkr.ecr.us-east-2.amazonaws.com/cloudsibyl-aws-data-collector:latest
```

### US East (N. Virginia) - us-east-1

```bash
# Login to ECR in us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 767397677341.dkr.ecr.us-east-1.amazonaws.com

# Tag the image for us-east-1
docker tag cloudsibyl-aws-data-collector:latest 767397677341.dkr.ecr.us-east-1.amazonaws.com/cloudsibyl-aws-data-collector:latest

# Push the image to us-east-1
docker push 767397677341.dkr.ecr.us-east-1.amazonaws.com/cloudsibyl-aws-data-collector:latest
```

## Step 3: Verify Deployment

After pushing to each region, you can verify the deployment:

```bash
# List repositories in each region
aws ecr describe-repositories --region ca-central-1
aws ecr describe-repositories --region us-east-2
aws ecr describe-repositories --region us-east-1

# List images in each repository
aws ecr describe-images --repository-name cloudsibyl-aws-data-collector --region ca-central-1
aws ecr describe-images --repository-name cloudsibyl-aws-data-collector --region us-east-2
aws ecr describe-images --repository-name cloudsibyl-aws-data-collector --region us-east-1
```

## Automated Deployment Script

You can also create a script to automate the deployment to all regions:

```bash
#!/bin/bash

# Set AWS profile
export AWS_DEFAULT_PROFILE=prod
export AWS_PROFILE=prod

# Array of regions
regions=("ca-central-1" "us-east-2" "us-east-1")

# Deploy to each region
for region in "${regions[@]}"; do
    echo "Deploying to region: $region"
    
    # Login to ECR
    aws ecr get-login-password --region $region | docker login --username AWS --password-stdin 767397677341.dkr.ecr.$region.amazonaws.com
    
    # Tag image
    docker tag cloudsibyl-aws-data-collector:latest 767397677341.dkr.ecr.$region.amazonaws.com/cloudsibyl-aws-data-collector:latest
    
    # Push image
    docker push 767397677341.dkr.ecr.$region.amazonaws.com/cloudsibyl-aws-data-collector:latest
    
    echo "Deployment to $region completed"
done

echo "All deployments completed successfully!"
```

## Notes

- Ensure your AWS credentials have the necessary permissions to push to ECR in all target regions
- The ECR repositories must exist in each region before pushing images
- Consider using AWS CLI profiles if you need to switch between different AWS accounts
- Monitor the deployment process for any authentication or permission errors
