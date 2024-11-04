from typing import List, Union
import os
import boto3
from logging import Logger as Log
from inspect import currentframe
import subprocess
import json
from time import sleep
from boto3 import client
import base64
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from _common import _common as _common_
from _engine import _engine as _engine_
from _util import _util_common as _util_common
import boto3

_WAIT_TIME_ = 4


def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


def get_ecr_login_password(aws_region: str = "us-east-1") -> tuple[str, str, str]:
    """Retrieves the Docker login credentials for Amazon ECR.

    :return: A tuple containing the username, password, and proxy endpoint.
    """
    ecr_client = aws_client("ecr", aws_region)

    try:
        # Retrieve the authorization token from ECR

        response = ecr_client.get_authorization_token()

        # Extract the authorization data
        auth_data = response.get("authorizationData")[0]
        auth_token = auth_data.get("authorizationToken")

        # Decode the base64-encoded authorization token
        decoded_token = base64.b64decode(auth_token).decode('utf-8')

        # Split the decoded token into username and password
        username, password = decoded_token.split(':')

        # Extract the proxy endpoint
        proxy_endpoint = auth_data.get("proxyEndpoint")

        return username, password, proxy_endpoint

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
        return None, None, None
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
        return None, None, None
    except ClientError as err:
        _common_.info_logger(f"Error: {err.response.get('Error', {}).get('Message')}")
        return None, None, None
    except KeyError as err:
        _common_.info_logger(f"Error: Key {err} not found in the response.")
        return None, None, None
    except Exception as err:
        _common_.info_logger(f"Unexpected error: {err}")
        return None, None, None


@_common_.exception_handler
def build_docker_image(repository_name: str,
                       aws_account_number: str,
                       dockerfile_filepath: str = "Dockerfile",
                       aws_region: str = "us-east-1",
                       path: str = ".") -> bool:

    # Build, tag, and push Docker image
    _common_.info_logger("Building Docker image...")

    print(f"repository_name: {repository_name}")

    build_cmd = f'docker build -f {dockerfile_filepath} -t {repository_name} {path}'
    print("test!!!!!!!%%%%%%", build_cmd)


    _engine_.run_command_progress(build_cmd)
    _common_.info_logger("Docker build completed.")

    # Tag Docker image
    _common_.info_logger("tagging docker image...")
    tag_cmd = f'docker tag {repository_name}:latest {aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:latest'
    _engine_.run_command_progress(tag_cmd)
    _common_.info_logger("tagging docker image is tagged.")


    # Push image to ECR
    _common_.info_logger("pushing docker image to ecr...")
    push_cmd = f'docker push {aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:latest'

    print(f"running command to push image to ecr: {push_cmd}")

    _engine_.run_command_progress(push_cmd)
    _common_.info_logger("pushing docker image is completed.")

    return True


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        dockerfile_filepath: str = "Dockerfile",
        lambda_function_name: str = None,
        lambda_function_role_name: str = None,
        api_gateway_api_name: str = None) -> bool:

    """this function is to setup ecr repository and build docker image

    Args:
        ecr_repository_name: ecr repository name
        aws_region: aws region
        aws_account_number: aws account number
        project_path: project path
        dockerfile_filepath: dockerfile path
        lambda_function_name: lambda function name
        lambda_function_role_name: lambda function role
        api_gateway_api_name: api gateway api name

    Returns:
        return True if the resources are created successfully, False otherwise


        # Stage 1: Build Stage
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

CMD ["python", "app.py"]


    """

    username, password, proxy_endpoint = get_ecr_login_password()

    # set environment variables
    os.environ['DOCKER_DEFAULT_PLATFORM'] = 'linux/amd64'
    _common_.info_logger("set default docker platform to linux/amd64")

    # login to ecr
    login_cmd = f'echo {password} | docker login --username AWS --password-stdin {aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com'
    login_process = _engine_.run_command_progress(login_cmd)
    _common_.info_logger("logging into ecr successfully.")

    build_docker_image(ecr_repository_name,
                       aws_account_number,
                       dockerfile_filepath,
                       aws_region,
                       path=project_path,
                       )
    return True


